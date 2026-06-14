# Ingestion Pipeline

Python pipeline that fetches daily stock prices from the Alpha Vantage API
and loads them into Snowflake as append-only raw rows.

## How it works

```
Alpha Vantage API
      │  TIME_SERIES_DAILY (last 100 trading days per ticker)
      ▼
api_client.py  ──►  parse JSON → list of tuples
      │
      ▼
db.py  ──►  read active tickers from APP.WATCHLIST
            insert rows into RAW.RAW_STOCK_PRICES
      │
      ▼
ingest_prices.py  ──►  orchestrates the full run
```

## Files

| File | Purpose |
|---|---|
| `ingest_prices.py` | Entry point — reads tickers, fetches prices, loads to Snowflake |
| `api_client.py` | Calls Alpha Vantage API, parses JSON into row tuples |
| `db.py` | Snowflake connection, active ticker query, batch insert |

## Design decisions

- **Append-only loading** — raw rows are never updated or deleted. Each row carries a `loaded_at` timestamp. dbt staging handles deduplication.
- **Rate limiting** — Alpha Vantage free tier allows 5 requests/minute. The pipeline waits 13 seconds between tickers to stay within limits.
- **Key-pair authentication** — Snowflake connection uses RSA key-pair auth (no passwords in code).
- **Project-root-relative paths** — `.env` and `rsa_key.p8` are always resolved from the project root regardless of where the script is run from.

## Running

```bash
# From the project root
python ingestion/ingest_prices.py
```

Expected output:
```
Connecting to Snowflake...
Reading active tickers from APP.WATCHLIST...
  Found 6 active tickers: ['AAPL', 'MSFT', 'GOOGL', 'JPM', 'SPY', 'ASTS']
Fetching prices for AAPL...
  Inserted 100 rows for AAPL
...
Done. Total rows inserted: 600
```
