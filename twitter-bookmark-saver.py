import asyncio
from playwright.async_api import async_playwright, Playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

async def setup_browser_and_page(playwright: Playwright):
    browser = await playwright.chromium.launch(
        channel="chrome",
        headless=False,
        args=[
            "--start-maximized",
            "--disable-notifications",
            # "--disable-blink-features=AutomationControlled" # Sometimes helps with detection
        ]
    )
    context = await browser.new_context(
        no_viewport=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    )
    page = await context.new_page()
    return browser, page

async def get_twitter_bookmark_links(page: Page):
    print("Please log in to Twitter/X and navigate to the 'Bookmarks' section.")
    input("Press Enter when you are on the 'Bookmarks' page and ready to start...")

    all_links = set() # Use a set directly to avoid duplicates
    processed_tweet_dom_elements_this_cycle = set() # To track DOM elements already seen in a scroll cycle

    TWEET_ARTICLE_SELECTOR = 'article[data-testid="tweet"]'
    TWEET_URL_IN_ARTICLE_SELECTOR = 'a:has(time[datetime])'

    SCROLL_PAUSE_TIME_MS = 3000 # More time for loading
    MAX_UNCHANGED_SCROLLS = 6 # Increased to give more opportunities
    
    last_scroll_height = await page.evaluate("document.body.scrollHeight")
    unchanged_scrolls_count = 0
    consecutive_fetch_errors = 0
    MAX_CONSECUTIVE_FETCH_ERRORS = 15 # Allow more individual errors if scrolling still loads content

    print("Starting to collect links...")

    while True:
        if consecutive_fetch_errors >= MAX_CONSECUTIVE_FETCH_ERRORS:
            print(f"Too many consecutive URL fetch errors ({MAX_CONSECUTIVE_FETCH_ERRORS}), stopping.")
            break
        
        # Wait for at least one tweet to be present before processing
        try:
            await page.wait_for_selector(TWEET_ARTICLE_SELECTOR, timeout=15000)
        except PlaywrightTimeoutError:
            print("No tweet articles found (or timeout waiting for the first one).")
            # If no tweets were found and there was no height change in the last cycle, it might be the end
            current_scroll_height = await page.evaluate("document.body.scrollHeight")
            if current_scroll_height == last_scroll_height and unchanged_scrolls_count >= MAX_UNCHANGED_SCROLLS -1:
                 print("It seems to be the end of the list or no more tweets to load after several attempts.")
                 break
            # If there are no tweets in the current view, count it as a scroll without new links/height
            unchanged_scrolls_count += 1
            print(f"Incrementing unchanged_scrolls_count to {unchanged_scrolls_count} for not finding visible tweets.")
            # Continue to the scroll block
        
        # Get all locators of tweets on the current VISIBLE page
        tweet_article_locators = await page.locator(TWEET_ARTICLE_SELECTOR).all()
        
        # Use a temporary set for new links found in this view
        new_links_found_this_scroll_cycle_set = set()
        tweets_processed_this_cycle = 0

        # Process only visible and unprocessed tweets in this pass
        for i, tweet_article_locator in enumerate(tweet_article_locators):
            try:
                 # Try to get an identifier for the DOM element to see if we've already seen it
                element_handle = await tweet_article_locator.element_handle()
                element_id = None
                if element_handle:
                    # Try data-tweetId, id, or bounding box as a fallback identifier
                    element_id = await element_handle.evaluate('(el) => el.dataset.tweetId || el.id || JSON.stringify(el.getBoundingClientRect())')
                
                if element_id and element_id in processed_tweet_dom_elements_this_cycle:
                    # print(f"  DOM element already processed in this cycle: {element_id}")
                    continue

                # Optional: Smooth scroll to the current element to ensure it's in view
                # if i % 10 == 0: # Every 10 visible tweets, a light scroll
                #     await tweet_article_locator.scroll_into_view_if_needed(timeout=3000)
                #     await page.wait_for_timeout(50)

                link_element_locator = tweet_article_locator.locator(TWEET_URL_IN_ARTICLE_SELECTOR).first
                
                tweet_url = None
                if await link_element_locator.count() > 0:
                    raw_url = await link_element_locator.get_attribute('href', timeout=2000)
                    if raw_url:
                        if raw_url.startswith("http"):
                            tweet_url = raw_url.split('?')[0] # Clean query params
                        elif raw_url.startswith("/"):
                            tweet_url = f"https://x.com{raw_url.split('?')[0]}"
                        
                if tweet_url:
                    if tweet_url not in all_links:
                        print(f"Link found: {tweet_url}")
                        all_links.add(tweet_url)
                        new_links_found_this_scroll_cycle_set.add(tweet_url)
                        consecutive_fetch_errors = 0 # Reset error counter
                    # else:
                        # print(f"  URL already collected: {tweet_url}")

                    if element_id: processed_tweet_dom_elements_this_cycle.add(element_id)
                    tweets_processed_this_cycle += 1

                else:
                    # If we couldn't extract the URL this way
                    # print(f"  Could not extract tweet URL for element at index {i}.")
                    # To avoid getting stuck on a problematic tweet, mark it as processed (DOM)
                    if element_id: processed_tweet_dom_elements_this_cycle.add(element_id)
                    consecutive_fetch_errors += 1


            except PlaywrightTimeoutError as e_timeout_tweet:
                #print(f"Timeout error processing tweet at index {i}: {e_timeout_tweet}")
                consecutive_fetch_errors += 1
                # Mark the DOM element as processed to avoid immediate retry
                try:
                    element_handle = await tweet_article_locator.element_handle()
                    if element_handle:
                         element_id = await element_handle.evaluate('(el) => el.dataset.tweetId || el.id || JSON.stringify(el.getBoundingClientRect())')
                         if element_id: processed_tweet_dom_elements_this_cycle.add(element_id)
                except:
                    pass # If even getting the handle or ID fails, continue


            except Exception as e_general_tweet:
                #print(f"GENERAL error processing tweet at index {i}: {e_general_tweet}")
                consecutive_fetch_errors += 1
                # Mark the DOM element as processed to avoid immediate retry
                try:
                    element_handle = await tweet_article_locator.element_handle()
                    if element_handle:
                         element_id = await element_handle.evaluate('(el) => el.dataset.tweetId || el.id || JSON.stringify(el.getBoundingClientRect())')
                         if element_id: processed_tweet_dom_elements_this_cycle.add(element_id)
                except:
                    pass # If even getting the handle or ID fails, continue


        # Scroll Logic and End of Page Detection
        num_new_links_found = len(new_links_found_this_scroll_cycle_set)
        print(f"Processing cycle: {num_new_links_found} new links found. Total: {len(all_links)} unique.")
        
        # Clear the set of processed DOM elements for the next scroll cycle
        processed_tweet_dom_elements_this_cycle.clear()

        current_scroll_height = await page.evaluate("document.body.scrollHeight")
        
        if num_new_links_found == 0:
            # If we didn't find new links in this view
            if current_scroll_height == last_scroll_height:
                unchanged_scrolls_count += 1
                print(f"Height did not change ({current_scroll_height}) AND no new links were found. Unchanged scrolls counter: {unchanged_scrolls_count}")
            else: # Height changed, but all new tweets were already collected or had no URL.
                  # Still, reset the counter because there was progress in content loading.
                unchanged_scrolls_count = 0
                print(f"Height changed (before:{last_scroll_height}, now:{current_scroll_height}) but no NEW links were found. Resetting unchanged scrolls counter.")
        else: # If we found new links, reset unchanged scrolls counter
            unchanged_scrolls_count = 0
            print(f"{num_new_links_found} new links found. Resetting unchanged scrolls counter.")


        if unchanged_scrolls_count >= MAX_UNCHANGED_SCROLLS:
            print(f"End of list reached (after {MAX_UNCHANGED_SCROLLS} scroll attempts without new links AND stable unchanged height).")
            break
        
        # Perform scrolling
        print("Scrolling...")
        
        # Method 1: Scroll with PageDown (better simulates human interaction)
        await page.focus('body') # Ensure body has focus for PageDown
        for _ in range(5): # Press PageDown multiple times, adjust number as needed
            await page.keyboard.press('PageDown')
            await page.wait_for_timeout(100) # Small pause between PageDowns

        # Method 2 (Alternative if PageDown doesn't work well): Direct scroll with JS
        # await page.evaluate(f"window.scrollBy(0, window.innerHeight * 0.9);") # Scroll 90% of window height

        await page.wait_for_timeout(SCROLL_PAUSE_TIME_MS) # Wait for new content to load

        # Update height for the next iteration
        last_scroll_height = await page.evaluate("document.body.scrollHeight")


    return list(all_links) # Convert set to list for output

async def main():
    async with async_playwright() as playwright:
        browser, page = await setup_browser_and_page(playwright)
        
        await page.goto("https://x.com", timeout=60000)

        try:
            saved_links = await get_twitter_bookmark_links(page)
            
            if saved_links:
                # The set already handles uniqueness
                unique_links = sorted(list(saved_links)) # Sort if consistent output is desired
                print(f"\n--- Total of {len(unique_links)} UNIQUE bookmarked tweet links found ---")
                for i, link in enumerate(unique_links):
                    print(f"{i+1}. {link}")
                
                with open("twitter_bookmarks_playwright_direct.txt", "w", encoding="utf-8") as f:
                    for link in unique_links:
                        f.write(link + "\n")
                print("\nLinks saved to 'twitter_bookmarks_playwright_direct.txt'")
            else:
                print("No bookmarked tweet links found.")

        except Exception as e:
            print(f"A general error occurred in main: {e}")
        finally:
            print("Closing the browser in 10 seconds...")
            await page.wait_for_timeout(10000) # Give user time to see final messages
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
