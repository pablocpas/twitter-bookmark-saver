# Twitter/X Bookmark Saver

This Python script uses Playwright to save all your bookmarked tweets (posts) from Twitter/X. It automates browser interaction to scroll through your bookmarks page and extract the direct links to each tweet.

## Features

*   Uses Playwright for robust browser automation.
*   Requires manual login to Twitter/X.
*   Automatically scrolls through the bookmarks page to load all items.
*   Extracts unique tweet URLs, removing query parameters.
*   Saves the collected links to a text file (`twitter_bookmarks_playwright_direct.txt`).
*   Provides console feedback during the scraping process.
*   Includes logic to detect the end of the bookmarks list.

## Prerequisites

*   Python 3.7+
*   Playwright library
*   A compatible browser (Chromium/Chrome is used by default)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pablocpas/twitter-bookmark-saver
    cd twitter-bookmark-saver
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    The script requires the Playwright library.
    ```bash
    pip install playwright
    ```

4.  **Install browser drivers:**
    Playwright needs browser binaries to work. This command installs the Chromium browser, which the script is configured to use.
    ```bash
    playwright install chrome
    # Or install all supported browsers:
    # playwright install
    ```

## Usage

1.  **Run the script:**
    ```bash
    python twitter_bookmark_saver.py
    ```

2.  **Log in manually:**
    A browser window will open. The script will navigate to `https://x.com`.
    You will be prompted:
    `Please log in to Twitter/X and navigate to the 'Bookmarks' section.`
    Manually log in with your credentials and then navigate to your "Bookmarks" page (usually found at `https://x.com/i/bookmarks`).

3.  **Start scraping:**
    Once you are on your Bookmarks page and the content has loaded, switch back to the terminal where the script is running.
    You will see the prompt:
    `Press Enter when you are on the 'Bookmarks' page and ready to start...`
    Press `Enter`.

4.  **Wait for completion:**
    The script will start scrolling down the page, collecting tweet links. You will see output in the console like:
    `Starting to collect links...`
    `Link found: https://x.com/username/status/12345...`
    `Processing cycle: X new links found. Total: Y unique.`
    `Scrolling...`

    This process can take some time depending on the number of bookmarks you have.

5.  **Retrieve results:**
    Once the script finishes, it will print the total number of unique links found and save them to a file named `twitter_bookmarks_playwright_direct.txt` in the same directory as the script.
    The script will wait for 10 seconds before closing the browser automatically.

## How it Works

1.  **Browser Setup:** Launches a non-headless Chromium browser instance with specific arguments to mimic a regular user and maximize the window.
2.  **User Interaction:** Prompts the user to log in and navigate to the bookmarks page manually. This is necessary because handling login programmatically can be complex and trigger security measures.
3.  **Scrolling & Data Extraction:**
    *   Once the user signals readiness, the script repeatedly scrolls down the bookmarks page using simulated 'PageDown' key presses.
    *   After each scroll, it waits for new content to load.
    *   It looks for tweet articles using the selector `article[data-testid="tweet"]`.
    *   For each article, it tries to extract the permalink URL from an `<a>` tag containing a `<time>` element (selector: `a:has(time[datetime])`).
    *   URLs are cleaned (query parameters removed) and stored in a `set` to ensure uniqueness.
4.  **End Detection:** The script attempts to detect the end of the bookmark list by monitoring:
    *   If no new links are found after several consecutive scroll attempts.
    *   If the page scroll height stops increasing.
    *   If too many consecutive errors occur while trying to fetch tweet data.
5.  **Output:** Saves all unique links to `twitter_bookmarks_playwright_direct.txt`.

## Important Notes & Troubleshooting

*   **UI Changes:** Twitter/X frequently updates its website structure. If the script stops working, the CSS selectors (`TWEET_ARTICLE_SELECTOR`, `TWEET_URL_IN_ARTICLE_SELECTOR`) might need to be updated.
*   **Rate Limiting:** Aggressive scraping can lead to temporary rate limiting or other restrictions from Twitter/X. The script includes pauses, but be mindful of usage.
*   **Headless Mode:** The script runs with `headless=False` (browser visible) to allow for manual login.
*   **Selectors:** The current selectors are based on observations of the X.com UI as of the script's creation. These are the most fragile part of any web saver.
*   **Error Handling:** The script has basic error handling for timeouts and issues while processing individual tweets but might not cover all edge cases.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (you'll need to create this file if you choose a license). A common choice is the MIT license.

---
