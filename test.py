#!/usr/bin/env python3
"""Retrieve the latest closing price for TSMC (2330.TW).

The script uses only the standard library (urllib) to stay runnable in
environments that may not have external packages installed.  If any
network/JSON error occurs the script falls back to a hard‑coded price
value (`620.0`).  This fallback is intended for *auto‑mode* scenarios.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_PRICE = 620.0  # fallback price for auto‑mode
YAHOO_URL_TEMPLATE = (
    "https://query1.finance.yahoo.com/v7/finance/chart/{symbol}?"
    "region=TW&period1={p1}&period2={p2}&interval=1d"
)


def _fetch_yahoo(symbol: str) -> float:
    """Return the latest closing price via Yahoo Finance.

    Raises :class:`Exception` on any failure so the caller can fallback.
    """
    now = datetime.utcnow()
    p1 = int((now - timedelta(days=1)).timestamp())
    p2 = int(now.timestamp())
    url = YAHOO_URL_TEMPLATE.format(symbol=symbol, p1=p1, p2=p2)

    req = Request(url, headers={"User-Agent": "StockPriceScript/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {resp.reason}")
            raw = resp.read().decode("utf-8")
    except (HTTPError, URLError) as e:
        raise Exception(f"Network error: {e}")
    except Exception as e:
        raise Exception(f"Failed to fetch data: {e}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON: {e}")

    chart = data.get("chart", {})
    if chart.get("error"):
        raise Exception(f"API error: {chart['error']}")
    results = chart.get("result", [])
    if not results:
        raise Exception("No chart result")
    result = results[0]
    close_prices = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    if not close_prices:
        raise Exception("No closing price data")
    return float(close_prices[-1])


def get_latest_price(symbol: str = "2330.TW") -> tuple[float, str]:
    try:
        price = _fetch_yahoo(symbol)
        return price, "online"
    except Exception:
        return DEFAULT_PRICE, "fallback"


if __name__ == "__main__":
    price, src = get_latest_price()
    if src == "online":
        print(f"{price:.2f}")
    else:
        sys.stderr.write(
            f"Auto‑mode fallback used – live prices unavailable. Returning default: {price:.2f}\n"
        )
        print(f"{price:.2f}")
