import json
import os
import re
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

SYMBOL = "NDX"
ASSET_CLASS = "INDEX"
API_URL = f"https://api.nasdaq.com/api/quote/{SYMBOL}/summary?assetclass={ASSET_CLASS}"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
    "Connection": "keep-alive",
}


def fetch_json(url: str) -> dict:
    print(f"[fetch] requesting {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
    except requests.exceptions.RequestException as exc:
        print(f"[fetch] request failed: {exc!r}")
        raise

    print(f"[fetch] HTTP {response.status_code}")
    raw_path = os.path.join(OUTPUT_DIR, "raw_response.json")
    try:
        data = response.json()
        with open(raw_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
    except ValueError:
        raw_path = os.path.join(OUTPUT_DIR, "raw_response.txt")
        with open(raw_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        response.raise_for_status()
        raise RuntimeError("Response was 200 but not valid JSON")

    response.raise_for_status()
    return data


def json_to_dataframe(data: dict) -> pd.DataFrame:
    summary = (data.get("data") or {}).get("summaryData") or {}
    if not summary:
        return pd.DataFrame()

    return pd.DataFrame([
        {"label": item.get("label", key), "value": item.get("value")}
        for key, item in summary.items()
    ])


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy().dropna(axis=0, how="all").dropna(axis=1, how="all")
    for column in df.select_dtypes(include=["object", "str"]).columns:
        df[column] = df[column].astype(str).str.strip()

    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in df.columns
    ]

    for column in df.columns:
        if df[column].dtype == object:
            cleaned = (
                df[column]
                .str.replace(r"[$,%]", "", regex=True)
                .str.replace(",", "", regex=False)
            )
            converted = pd.to_numeric(cleaned, errors="coerce")
            if converted.notna().mean() > 0.5:
                df[column] = converted

    df = df.drop_duplicates().reset_index(drop=True)
    df["scraped_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return df


def save_csv(df: pd.DataFrame, filename: str = "nasdaq_ndx_clean.csv") -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    print(f"[save] wrote {len(df)} rows to {path}")


def main() -> None:
    data = fetch_json(API_URL)
    raw_df = json_to_dataframe(data)
    if raw_df.empty:
        print("[warn] no structured data extracted; inspect raw_response.json")
        sys.exit(1)

    clean_df = clean_dataframe(raw_df)
    print(clean_df.head(20))
    save_csv(clean_df)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
