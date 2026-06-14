# MarketPulse Analytics

A end-to-end **data engineering portfolio project** built on the modern data stack.
MarketPulse ingests daily stock prices, transforms them with dbt, and exposes
analytics-ready models for business intelligence — with a Streamlit app for
watchlist management.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Ingestion | Python 3.11, Alpha Vantage API |
| Storage | Snowflake |
| Transformation | dbt Core + dbt-snowflake |
| Watchlist App | Streamlit |
| BI (planned) | Power BI |
| Environment | Anaconda, python-dotenv |

---

## Architecture

```
Alpha Vantage API
      │
      ▼
Python Ingestion ──────────► Snowflake RAW.RAW_STOCK_PRICES
(ingestion/)                        │
                                    │
Streamlit App ────────────► Snowflake APP.WATCHLIST
(app/)                              │
                                    ▼
                             dbt Transformations
                             ┌─────────────────────────────┐
                             │  STAGING                    │
                             │  stg_market__stock_prices   │
                             │  stg_market__tickers        │
                             ├─────────────────────────────┤
                             │  INTERMEDIATE               │
                             │  int_stock_daily_returns    │
                             │  int_stock_moving_averages  │
                             │  int_stock_volatility       │
                             ├─────────────────────────────┤
                             │  MARTS                      │
                             │  dim_ticker                 │
                             │  dim_date                   │
                             │  fact_stock_price_daily     │
                             │  fact_stock_performance_    │
                             │  mart_watchlist_performance │
                             │  mart_ticker_perf_summary   │
                             └─────────────────────────────┘
                                    │
                                    ▼
                              Power BI (planned)
```

---

## What This Project Demonstrates

### Data Engineering
- **API ingestion pipeline** with rate-limit handling and append-only raw loading
- **Snowflake** schema design across RAW, STAGING, INTERMEDIATE, MARTS, and SEMANTIC layers
- **Key-pair authentication** for secure Snowflake connectivity
- **Modular Python** with separation of concerns (connection, API client, orchestration)

### dbt Best Practices
- Full **layered architecture**: sources → staging → intermediate → marts
- **Star schema** dimensional modelling: dims, facts, and finance marts
- **Window functions**: LAG for daily returns, rolling AVG for moving averages, STDDEV for volatility
- **Custom macros**: `safe_divide` for null-safe division, `generate_schema_name` for clean schema routing
- **Data quality tests** on every model: `not_null`, `unique`, `accepted_values`, `relationships`
- **Seed files** for NYSE market holidays powering trading-day logic in `dim_date`
- Full **YAML documentation** with column descriptions on all models

### Application Development
- **Streamlit** watchlist management app with CRUD operations
- Soft-delete pattern with reactivation logic
- Snowflake key-pair auth from a Python web app

---

## Project Structure

```
marketpulse-analytics/
├── app/                    # Streamlit watchlist management app
├── dbt/                    # dbt project — all transformations
│   ├── macros/             # Reusable SQL macros
│   ├── models/
│   │   ├── sources/        # Raw source definitions
│   │   ├── staging/        # Cleaned, typed, deduplicated views
│   │   ├── intermediate/   # Business logic (returns, MAs, volatility)
│   │   └── marts/          # Analytics-ready tables for BI
│   │       ├── core/       # Dims and facts
│   │       └── finance/    # Business-facing mart models
│   └── seeds/              # NYSE market holiday reference data
├── ingestion/              # Python API ingestion pipeline
├── snowflake/              # Manual Snowflake setup scripts
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

---

## Snowflake Schema Design

| Schema | Purpose |
|---|---|
| `RAW` | Append-only raw data from APIs and seeds. Never modified. |
| `APP` | Tables owned by the Streamlit application (watchlist). |
| `STAGING` | Cleaned, typed, deduplicated views built by dbt. |
| `INTERMEDIATE` | Business logic: returns, moving averages, volatility. |
| `MARTS` | Analytics-ready dimensional models for Power BI. |
| `SEMANTIC` | Governed metric views (planned for M4). |

---

## dbt Models

### Staging
| Model | Description |
|---|---|
| `stg_market__stock_prices` | Cleans and deduplicates raw OHLCV price data |
| `stg_market__tickers` | Cleans watchlist tickers from the app schema |

### Intermediate
| Model | Description |
|---|---|
| `int_stock_daily_returns` | Daily price change and % return using LAG() |
| `int_stock_moving_averages` | 7, 20, and 50-day moving averages |
| `int_stock_volatility` | 20-day rolling volatility, annualized |

### Marts — Core
| Model | Description |
|---|---|
| `dim_ticker` | Ticker dimension with company metadata |
| `dim_date` | Full calendar 2024–2027 with NYSE trading day flags |
| `fact_stock_price_daily` | Core OHLCV fact table |
| `fact_stock_performance_daily` | Performance metrics joined from intermediate models |

### Marts — Finance
| Model | Description |
|---|---|
| `mart_watchlist_performance` | Denormalized daily view for Power BI watchlist reports |
| `mart_ticker_performance_summary` | Per-ticker stats across 6 time periods (YTD, MTD, 30D, 90D, 1Y, ALL) |

---

## Getting Started

### Prerequisites
- Anaconda or Miniconda
- Snowflake account (free trial works)
- Alpha Vantage API key (free tier)

### Setup

```bash
# 1. Create and activate the conda environment
conda create -n marketpulse python=3.11 -y
conda activate marketpulse
pip install -r requirements.txt

# 2. Copy and fill in your credentials
cp .env.example .env

# 3. Run Snowflake setup scripts (in order, via Snowflake worksheet)
#    snowflake/00_role_and_warehouse.sql
#    snowflake/01_database_and_schemas.sql
#    snowflake/02_app_watchlist.sql
#    snowflake/03_raw_stock_prices.sql

# 4. Ingest stock prices
python ingestion/ingest_prices.py

# 5. Run dbt transformations
cd dbt
dbt seed
dbt build

# 6. Launch the Streamlit app
cd ..
python -m streamlit run app/app.py
```

---

## Data Quality

Every dbt model is tested with a combination of:
- **not_null** — core keys and measures are never null
- **unique** — grain is enforced at every layer
- **accepted_values** — categorical fields are validated
- **relationships** — foreign keys to dims are verified
- **79 total tests passing** across the full pipeline

---

## Author

Andres Vega | [LinkedIn](https://linkedin.com/in/andres-vega-icaza) | andres.vega.icaza@gmail.com
