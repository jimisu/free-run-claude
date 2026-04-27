#!/usr/bin/env python3
import requests, datetime, json, sys

# Query today's stock price for 2330.TW (Taiwan's TSMC) using Yahoo Finance API
stock_symbol = "2330.TW"
# Compute timestamps for previous day and now
period1 = int((datetime.datetime.utcnow() - datetime.timedelta(days=1)).timestamp())
period2 = int(datetime.datetime.utcnow().timestamp())
url = f"https://query1.finance.yahoo.com/v7/finance/chart/{stock_symbol}?region=TW&period1={period1}&period2={period2}&interval=1d"

try:
    resp = requests.get(url)
    data = resp.json()
    if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result'])>0:
        result = data['chart']['result'][0]
        if ('timestamp' in result and 'indicators' in result and 'quote' in result['indicators'] and
                result['indicators']['quote'][0]['close']):
            close_price = result['indicators']['quote'][0]['close'][-1]
            print(f"{stock_symbol} closing price (today): {close_price}")
        else:
            raise ValueError("Unexpected data structure")
    else:
        raise ValueError('No chart result')
except Exception as e:
    print(f"Error fetching price: {e}", file=sys.stderr)
    sys.exit(1)
