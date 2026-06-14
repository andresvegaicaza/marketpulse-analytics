"""Main ingestion script: read tickers → fetch prices → load to Snowflake."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_connection, get_active_tickers, insert_prices
from api_client import fetch_daily_prices


def main():
    print("Connecting to Snowflake...")
    conn = get_connection()

    print("Reading active tickers from APP.WATCHLIST...")
    tickers = get_active_tickers(conn)
    print(f"  Found {len(tickers)} active tickers: {tickers}")

    total_rows = 0
    for i, symbol in enumerate(tickers):
        print(f"Fetching prices for {symbol}...")
        rows = fetch_daily_prices(symbol)

        if rows:
            insert_prices(conn, rows)
            print(f"  Inserted {len(rows)} rows for {symbol}")
            total_rows += len(rows)
        else:
            print(f"  Skipped {symbol} — no data")

        # Alpha Vantage free tier: 5 requests/minute. Wait between calls.
        if i < len(tickers) - 1:
            time.sleep(13)

    conn.close()
    print(f"\nDone. Total rows inserted: {total_rows}")


if __name__ == "__main__":
    main()
