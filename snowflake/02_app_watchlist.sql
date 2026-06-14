-- Run as MARKETPULSE_ROLE
-- Creates APP.WATCHLIST and seeds 5 starter tickers

USE ROLE MARKETPULSE_ROLE;
USE DATABASE MARKETPULSE_DEV;
USE SCHEMA APP;
USE WAREHOUSE MARKETPULSE_WH;

CREATE TABLE IF NOT EXISTS APP.WATCHLIST (
    watchlist_id    NUMBER AUTOINCREMENT PRIMARY KEY,
    symbol          VARCHAR(10)   NOT NULL UNIQUE,
    company_name    VARCHAR(255),
    category        VARCHAR(100),
    notes           VARCHAR(1000),
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    updated_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
);

-- Seed 5 tickers
INSERT INTO APP.WATCHLIST (symbol, company_name, category, notes)
SELECT * FROM VALUES
    ('AAPL', 'Apple Inc.',           'Tech',    'Core holding'),
    ('MSFT', 'Microsoft Corporation','Tech',    'Cloud & AI exposure'),
    ('GOOGL','Alphabet Inc.',        'Tech',    'Advertising + AI'),
    ('JPM',  'JPMorgan Chase & Co.', 'Finance', 'Large-cap bank'),
    ('SPY',  'SPDR S&P 500 ETF',     'ETF',     'Benchmark index'),
    ('ASTS',  'AST SpaceMobile, Inc.',    'Space',     ' Communication Equipment / Wireless Telecommunications')
AS v(symbol, company_name, category, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM APP.WATCHLIST w WHERE w.symbol = v.symbol
);

-- Verify
SELECT * FROM APP.WATCHLIST;
