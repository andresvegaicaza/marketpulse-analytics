"""Fetch daily stock prices from Alpha Vantage TIME_SERIES_DAILY."""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "https://www.alphavantage.co/query"


def fetch_daily_prices(symbol: str) -> list[tuple]:
    """Fetch the most recent daily prices for a ticker from Alpha Vantage.

    Uses outputsize=compact which returns the last 100 trading days.
    Returns a list of tuples:
        (symbol, trade_date, open, high, low, close, volume, source)
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": os.getenv("ALPHAVANTAGE_API_KEY"),
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        note = data.get("Note") or data.get("Information") or data
        print(f"  Warning: unexpected response for {symbol}: {note}")
        return []

    rows = []
    for date_str, values in data["Time Series (Daily)"].items():
        rows.append((
            symbol,
            date_str,
            float(values["1. open"]),
            float(values["2. high"]),
            float(values["3. low"]),
            float(values["4. close"]),
            int(values["5. volume"]),
            "alpha_vantage",
        ))

    return rows
