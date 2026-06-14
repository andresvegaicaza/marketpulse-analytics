# dbt Project — MarketPulse Transformations

dbt Core project that transforms raw stock price data into analytics-ready
dimensional models in Snowflake. Built following dbt best practices with
full documentation, testing, and a clean layered architecture.

## Running

```bash
cd dbt

dbt debug          # verify connection
dbt seed           # load NYSE market holidays reference data
dbt build          # run all models + all tests in dependency order
dbt docs generate  # build documentation site
dbt docs serve     # open lineage graph in browser
```

## Layer architecture

```
sources  (raw Snowflake tables)
   │
   ▼
staging  (STAGING schema — views)
   clean, rename, cast, deduplicate
   │
   ▼
intermediate  (INTERMEDIATE schema — views)
   business logic: returns, moving averages, volatility
   │
   ▼
marts/core  (MARTS schema — tables)
   dim_ticker, dim_date, fact_stock_price_daily, fact_stock_performance_daily
   │
   ▼
marts/finance  (MARTS schema — tables)
   mart_watchlist_performance, mart_ticker_performance_summary
```

## Key design decisions

**Explicit columns everywhere** — no `SELECT *` in any model except the final `SELECT * FROM final` CTE pattern.

**Custom macros**
- `safe_divide(numerator, denominator)` — null-safe division used for all percentage calculations
- `generate_schema_name(custom_schema_name, node)` — routes models to the correct schema without name concatenation

**Trading-day awareness** — `dim_date` is a full calendar (2024–2027) with `is_trading_day`, `previous_trading_date`, and `next_trading_date` flags derived from the `market_holidays` seed (NYSE full-day closures).

**Star schema** — `dim_ticker` and `dim_date` connect to fact tables via `ticker_symbol` and `date_key`, enabling clean Power BI relationships.

## Test coverage

79 tests passing across the full pipeline:
- `not_null` on all key columns and measures
- `unique` on all primary keys and grains
- `accepted_values` on categorical fields
- `relationships` from facts to dims
- 6 time-period variants in `mart_ticker_performance_summary`

## Folder structure

```
dbt/
├── macros/
│   ├── generate_schema_name.sql
│   └── safe_divide.sql
├── models/
│   ├── sources/
│   │   └── market_sources.yml
│   ├── staging/market/
│   │   ├── stg_market__stock_prices.sql
│   │   ├── stg_market__tickers.sql
│   │   └── _market__models.yml
│   ├── intermediate/market/
│   │   ├── int_stock_daily_returns.sql
│   │   ├── int_stock_moving_averages.sql
│   │   ├── int_stock_volatility.sql
│   │   └── _market__models.yml
│   └── marts/
│       ├── core/
│       │   ├── dim_ticker.sql
│       │   ├── dim_date.sql
│       │   ├── fact_stock_price_daily.sql
│       │   ├── fact_stock_performance_daily.sql
│       │   └── _core__models.yml
│       └── finance/
│           ├── mart_watchlist_performance.sql
│           ├── mart_ticker_performance_summary.sql
│           └── _finance__models.yml
└── seeds/
    └── market_holidays.csv
```
