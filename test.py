#!/usr/bin/env python3
"""A lightweight auto‑mode script to show the latest TSMC price.

In environments where outbound HTTP is blocked (e.g. auto‑mode “offline”), the
script falls back to a hard‑coded example value instead of failing with a
network error.
"""

import datetime
import sys
import time

MAX_RETRIES = 3  # number of retry attempts for network call
RETRY_DELAY = 2   # seconds to wait between retries

try:
    import requests  # pragma: no cover
except Exception:  # pragma: no cover
    requests = None

# --------------------------------------------------
# Helper – fetch price via Yahoo Finance API (online)
# --------------------------------------------------

def _fetch_online() -> float:
    """Fetch the latest closing price from Yahoo Finance with retry logic.
    Retries up to ``MAX_RETRIES`` times if a transient network error occurs.
    """
    if not requests:  # pragma: no cover
        raise RuntimeError("requests library not available")

    stock_symbol = "2330.TW"
    now = datetime.datetime.utcnow()
    period1 = int((now - datetime.timedelta(days=1)).timestamp())
    period2 = int(now.timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/chart/{stock_symbol}?"
        f"region=TW&period1={period1}&period2={period2}&interval=1d"
    )
    headers = {"User-Agent": "StockPriceScript/1.0"}

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            break
        # 非 200 代表可能是暫時性問題，稍等後重試
        print(f"[Retry {attempt}] HTTP {resp.status_code}: {resp.reason}", file=sys.stderr)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    else:
        raise ValueError(f"Failed after {MAX_RETRIES} attempts, last status: {resp.status_code}")

    if not resp.text.strip():
        raise ValueError("Empty response from Yahoo Finance")

    data = resp.json()
    chart = data.get("chart", {})
    if chart.get("error"):
        raise ValueError(f"API error: {chart['error']}")
    result_list = chart.get("result", [])
    if not result_list:
        raise ValueError("No chart result")
    result = result_list[0]
    close_prices = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    if not close_prices:
        raise ValueError("No closing price data")
    return float(close_prices[-1])

# --------------------------------------------------
# Public API – returns (price, source)
# --------------------------------------------------

def get_latest_price() -> tuple[float, str]:
    """Return the latest price fetched from Yahoo Finance.
    If the request fails, the exception is propagated so the caller can see the error.
    """
    price = _fetch_online()
    return price, "online"

# --------------------------------------------------
# CLI behaviour – just print to stdout
# --------------------------------------------------
if __name__ == "__main__":
    try:
        price, src = get_latest_price()
        print(f"2330.TW closing price (today, online): {price}")
    except Exception as e:
        print("⚠️ 取得價格失敗:", e, file=sys.stderr)
        sys.exit(1)
