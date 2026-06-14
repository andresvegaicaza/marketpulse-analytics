# Streamlit Watchlist App

A lightweight web app for managing the MarketPulse stock watchlist.
Built with Streamlit and connected directly to Snowflake via key-pair auth.

## Features

- **View watchlist** — see all active tickers with company name, category, notes, and timestamps
- **Add ticker** — add a new ticker with optional metadata
- **Reactivation logic** — re-adding a previously deactivated ticker reactivates it instead of inserting a duplicate
- **Edit ticker** — update company name, category, and notes
- **Deactivate / Reactivate** — soft-delete pattern, no hard deletes

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — three tabs: Watchlist, Add Ticker, Manage Ticker |
| `db.py` | Snowflake connection and all CRUD operations for APP.WATCHLIST |

## Running

```bash
# From the project root
python -m streamlit run app/app.py
```

Then open http://localhost:8501 in your browser.

## Database table

The app reads from and writes to `MARKETPULSE_DEV.APP.WATCHLIST`.

| Column | Type | Notes |
|---|---|---|
| `watchlist_id` | autoincrement | Primary key |
| `symbol` | string | Unique ticker symbol |
| `company_name` | string | Optional |
| `category` | string | User-defined tag |
| `notes` | string | Free text |
| `is_active` | boolean | Soft-delete flag |
| `created_at` | timestamp | Set on insert |
| `updated_at` | timestamp | Set explicitly on every update |
