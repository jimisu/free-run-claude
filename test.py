#!/usr/bin/env python3
import requests, datetime, sys

# --------------------------------------------
# Query today's stock price for 2330.TW (TSMC)
# --------------------------------------------

stock_symbol = "2330.TW"

# Current UTC timestamp
now = datetime.datetime.utcnow()
# Timestamp for 24 hours ago (previous trading day UTC)
period1 = int((now - datetime.timedelta(days=1)).timestamp())
period2 = int(now.timestamp())
url = f"https://query1.finance.yahoo.com/v7/finance/chart/{stock_symbol}?region=TW&period1={period1}&period2={period2}&interval=1d"

headers = {
    "User-Agent": "StockPriceScript/1.0"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()          # Raise if not 200
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
    close_price = close_prices[-1]
    print(f"{stock_symbol} closing price (today): {close_price}")
except Exception as err:
    print(f"Error fetching price: {err}", file=sys.stderr)
    sys.exit(1)
