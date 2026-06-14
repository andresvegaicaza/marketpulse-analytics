# Snowflake Setup Scripts

Manual SQL scripts to set up the Snowflake environment from scratch.
Run these once in a Snowflake worksheet in the order listed below.

## Execution order

| Script | What it does | Run as |
|---|---|---|
| `00_role_and_warehouse.sql` | Creates `MARKETPULSE_ROLE`, `MARKETPULSE_WH`, assigns them to your user, and registers your RSA public key for key-pair auth | `ACCOUNTADMIN` |
| `01_database_and_schemas.sql` | Creates `MARKETPULSE_DEV` database and all 6 schemas (`APP`, `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, `SEMANTIC`) | `ACCOUNTADMIN` then `MARKETPULSE_ROLE` |
| `02_app_watchlist.sql` | Creates `APP.WATCHLIST` table and seeds 6 starter tickers | `MARKETPULSE_ROLE` |
| `03_raw_stock_prices.sql` | Creates `RAW.RAW_STOCK_PRICES` append-only table | `MARKETPULSE_ROLE` |

## Schema overview

| Schema | Owner | Purpose |
|---|---|---|
| `APP` | Streamlit app | Watchlist management table |
| `RAW` | Python ingestion | Append-only raw data from APIs |
| `STAGING` | dbt | Cleaned and typed views |
| `INTERMEDIATE` | dbt | Business logic views |
| `MARTS` | dbt | Analytics-ready tables for Power BI |
| `SEMANTIC` | dbt (planned) | Governed metric views |
