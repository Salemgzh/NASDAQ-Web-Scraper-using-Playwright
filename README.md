# Nasdaq-100 Index Quote Scraper

A small Playwright-based scraper that renders the Nasdaq-100 quotes page (a JavaScript-heavy site) and saves the fully rendered HTML plus a full-page screenshot for inspection or downstream parsing.

## Problem

The [Nasdaq-100 quotes page](https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index) renders its data table client-side with JavaScript. A plain HTTP request (e.g. `requests.get()`) only returns the initial skeleton HTML — the table of symbols, prices, and percentage changes is never present in the response, making the page impossible to scrape with simple request-based tools.

## Solution

This script uses **Playwright** to drive a real (headless) Firefox browser, load the page, wait for the JavaScript to finish rendering the quote table, and then capture:

1. The fully rendered DOM as static HTML.
2. A full-page screenshot of the rendered page.

Both artifacts can then be parsed offline (e.g. with `pandas.read_html()` or `lxml`) without needing to keep re-launching a browser.

## Features

- Headless Firefox automation via Playwright's sync API
- Custom desktop User-Agent string to reduce the chance of being served a bot-blocked/blank page
- Explicit wait (`page.wait_for_timeout`) to allow client-side rendering to complete after `domcontentloaded`
- Saves rendered output as:
  - `playwright.html` — full page source, UTF-8 encoded
  - `screenshot.png` — full-page (not just viewport) screenshot
- Minimal dependencies, single-file script

## Installation

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install playwright pandas lxml

# 3. Install the Playwright browser binaries
playwright install firefox
```

## Example

Run the scraper directly:

```bash
python scrapy.py
```

```python
import pandas as pd
import lxml
from playwright.sync_api import sync_playwright

url = "https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    context = browser.new_context(user_agent=USER_AGENT)
    page = context.new_page()

    page.goto(url, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(5000)  # let JS finish rendering

    content = page.content()
    with open("playwright.html", "w", encoding="utf-8") as file:
        file.write(content)

    page.screenshot(path="screenshot.png", full_page=True)
    browser.close()
```

To turn the saved HTML into a DataFrame afterward:

```python
import pandas as pd

tables = pd.read_html("playwright.html")
df = tables[0]   # adjust index to match the quotes table
print(df.head())
```

## Screenshot

`screenshot.png` is a full-page capture of the rendered Nasdaq-100 quotes page, including the symbol/name/market cap/last sale/net change/percentage change table for all index constituents (AAPL through XEL), the cookie consent banner, and the page footer.

## Output

Running the script produces two files in the working directory:

| File | Description |
|---|---|
| `playwright.html` | Full rendered HTML (~2,300 lines / ~310 KB) of the quotes page, including the complete data table markup |
| `screenshot.png` | Full-page PNG screenshot (~700 KB) of the same rendered page |

The HTML contains a `<table>` with columns: **Symbol, Name, Market Cap, Last Sale, Net Change, Percentage Change**, along with a timestamp footer (e.g. "Aug 18, 2026 12:16 PM") indicating when the quotes were last updated.

## Limitations

- **Fixed wait, not a real readiness check**: the 5-second `wait_for_timeout` is a guess. On a slow connection the table may not have finished loading; on a fast one, time is wasted. A more robust approach would wait for a specific selector (e.g. the table element) to appear.
- **No error handling**: navigation timeouts, missing selectors, or a changed page layout will raise unhandled exceptions and halt the script.
- **Cookie consent banner not dismissed**: the screenshot and HTML include the "Accept All Cookies" overlay, which can obscure content in the screenshot and may interfere with table parsing if not filtered out.
- **Fragile to site changes**: Nasdaq can change its DOM structure, table layout, or add stronger bot detection at any time, breaking parsing or blocking the request entirely.
- **No rate limiting / retry logic**: repeated runs in quick succession may trigger rate limiting or IP-based blocking.
- **Single page only**: the script scrapes one fixed URL; it isn't parameterized for other tickers, indices, or pagination.
- **Data staleness**: prices are a snapshot at scrape time (e.g. "Aug 18, 2026 12:16 PM" in this run) and are not live/real-time beyond that moment.
- **Legal/ToS considerations**: scraping Nasdaq.com may be subject to their Terms of Service; this script is intended for personal/educational use, not redistribution or commercial use of the data.
