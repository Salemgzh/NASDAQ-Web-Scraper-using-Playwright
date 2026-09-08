# Nasdaq-100 Index Data Scraper

A small Python project that evolved from browser-based scraping to direct API extraction of Nasdaq-100 (NDX) data.

## Evolution

This repository intentionally keeps the two approaches as distinct stages rather than presenting the final implementation as if it appeared fully formed.

### v1 — Playwright rendering

The first implementation used Playwright with headless Firefox to load Nasdaq's JavaScript-heavy quote page and save the rendered HTML and a screenshot. The original implementation and captured artifacts are preserved under `v1_playwright/`.

The key lesson from v1 was that the visible quote table was populated by a runtime web component. Saving `page.content()` did not provide a reliable structured-data source for downstream parsing.

### v2 — API pivot

The second implementation moved to the JSON endpoint used by Nasdaq's frontend:

`https://api.nasdaq.com/api/quote/NDX/summary?assetclass=INDEX`

Instead of launching a browser, v2 requests the JSON directly, extracts `data.summaryData`, cleans it with Pandas, adds a UTC scrape timestamp, and writes a CSV. This removes the browser dependency and turns the scraper into an explicit fetch → extract → clean → save pipeline.

## Repository layout

```text
.
├── v1_playwright/
│   ├── scrapy.py
│   ├── playwright.html
│   └── screenshot.png
│
└── v2_api/
    ├── scrapy.py
    ├── requirements.txt
    ├── raw_response.json
    └── nasdaq_ndx_clean.csv
```

## Running v1

```bash
pip install playwright pandas lxml
playwright install firefox
python v1_playwright/scrapy.py
```

v1 is retained as a historical/reference implementation.

## Running v2

```bash
pip install -r v2_api/requirements.txt
python v2_api/scrapy.py
```

The API implementation writes its output beside the script and records the raw response before transforming it.

## v2 pipeline

```text
Nasdaq JSON API
      ↓
 raw_response.json
      ↓
 data.summaryData
      ↓
 Pandas DataFrame
      ↓
 cleaning + type conversion
      ↓
 nasdaq_ndx_clean.csv
```

The script is configured near the top of `v2_api/scrapy.py` with `SYMBOL` and `ASSET_CLASS`, so the same pattern can be adapted to other Nasdaq instruments where the endpoint supports them.

## What changed

| | v1 | v2 |
|---|---|---|
| Acquisition | Playwright + Firefox | `requests` |
| Source | Rendered Nasdaq page | Nasdaq JSON API |
| Main artifact | Rendered HTML + screenshot | Raw JSON + cleaned CSV |
| Structured extraction | Not reliable from saved DOM | `data.summaryData` |
| Browser dependency | Required | Not required |
| Data processing | Manual/offline follow-up | Pandas pipeline |

## Notes

Nasdaq can change its frontend, API behavior, response schema, or access controls. The v1 implementation is kept because it documents the original problem-solving path; v2 is the current implementation.

Use the scraper responsibly and check Nasdaq's applicable terms before using retrieved data beyond personal or educational purposes.
