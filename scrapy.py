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

    context = browser.new_context(
        user_agent=USER_AGENT
    )

    page = context.new_page()

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=50000
    )

    # Give JavaScript time to render
    page.wait_for_timeout(5000)

    # Save rendered HTML
    content = page.content()

    with open("playwright.html", "w", encoding="utf-8") as file:
        file.write(content)

    # Screenshot
    page.screenshot(
        path="screenshot.png",
        full_page=True
    )

    browser.close()