#!/usr/bin/env python3
"""
Fetch past year's TSMC (2330) stock price and institutional investors buy/sell data
using FinMind API.

Usage:
    python finmind_tsmc.py [--token YOUR_TOKEN] [--output-dir ./data]

If token is provided, it will be added to requests for higher rate limits.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests

API_URL = "https://api.finmindtrade.com/api/v4/data"

# Date range: past year from today
TODAY = dt.date.today()
ONE_YEAR_AGO = TODAY - dt.timedelta(days=365)


def fetch_finmind_dataset(
    dataset: str,
    data_id: str,
    start_date: str,
    end_date: str,
    token: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch data from FinMind API for a given dataset.

    Parameters
    ----------
    dataset: str
        Dataset name, e.g. "TaiwanStockPrice" or "TaiwanStockInstitutionalInvestorsBuySell".
    data_id: str
        Stock ID, e.g. "2330".
    start_date: str
        Start date in YYYY-MM-DD format.
    end_date: str
        End date in YYYY-MM-DD format.
    token: str | None
        Optional FinMind token for higher rate limits.

    Returns
    -------
    List[Dict]
        List of records returned by the API.
    """
    params = {
        "dataset": dataset,
        "data_id": data_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    if token:
        params["token"] = token

    print(f"Fetching {dataset} for {data_id} from {start_date} to {end_date}...")
    resp = requests.get(API_URL, params=params, timeout=30)
    if resp.status_code != 200:
        print(
            f"Error: API request failed with status {resp.status_code}: {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    data = resp.json()
    if data.get("status") != 200:
        print(
            f"Error: FinMind returned error status: {data.get('msg')}",
            file=sys.stderr,
        )
        sys.exit(1)

    records = data.get("data", [])
    print(f"  -> Received {len(records)} records.")
    return records


def save_json(data: List[Dict], filepath: str) -> None:
    """Save data as JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} records to {filepath}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch TSMC stock price and institutional investor data from FinMind"
    )
    parser.add_argument(
        "--token",
        help="FinMind API token (optional, increases rate limit)",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save output JSON files",
        default="./finmind_data",
    )
    args = parser.parse_args()

    start_date = ONE_YEAR_AGO.isoformat()
    end_date = TODAY.isoformat()
    stock_id = "2330"

    # Fetch TaiwanStockPrice (daily price)
    price_data = fetch_finmind_dataset(
        dataset="TaiwanStockPrice",
        data_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=args.token,
    )
    save_json(
        price_data,
        os.path.join(args.output_dir, f"{stock_id}_price_{start_date}_{end_date}.json"),
    )

    # Fetch TaiwanStockInstitutionalInvestorsBuySell (三大法人買賣超)
    inst_data = fetch_finmind_dataset(
        dataset="TaiwanStockInstitutionalInvestorsBuySell",
        data_id=stock_id,
        start_date=start_date,
        end_date=end_date,
        token=args.token,
    )
    save_json(
        inst_data,
        os.path.join(
            args.output_dir, f"{stock_id}_institutional_{start_date}_{end_date}.json"
        ),
    )

    # Optional: also save as CSV for easy inspection
    try:
        import pandas as pd

        price_df = pd.DataFrame(price_data)
        if not price_df.empty:
            price_df.to_csv(
                os.path.join(
                    args.output_dir,
                    f"{stock_id}_price_{start_date}_{end_date}.csv",
                ),
                index=False,
            )
        inst_df = pd.DataFrame(inst_data)
        if not inst_df.empty:
            inst_df.to_csv(
                os.path.join(
                    args.output_dir,
                    f"{stock_id}_institutional_{start_date}_{end_date}.csv",
                ),
                index=False,
            )
        print("CSV files also saved (pandas available).")
    except ImportError:
        print("Pandas not installed; skipping CSV export.")


if __name__ == "__main__":
    main()