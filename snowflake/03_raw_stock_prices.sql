-- Run as MARKETPULSE_ROLE
-- Creates the append-only raw price table

USE ROLE MARKETPULSE_ROLE;
USE DATABASE MARKETPULSE_DEV;
USE SCHEMA RAW;
USE WAREHOUSE MARKETPULSE_WH;

CREATE TABLE IF NOT EXISTS RAW.RAW_STOCK_PRICES (
    symbol      VARCHAR(10)   NOT NULL,
    trade_date  DATE          NOT NULL,
    open        FLOAT,
    high        FLOAT,
    low         FLOAT,
    close       FLOAT,
    volume      NUMBER,
    source      VARCHAR(50)   NOT NULL DEFAULT 'alpha_vantage',
    loaded_at   TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
    -- No PK enforced — dedupe happens in dbt staging
);

-- Verify
DESCRIBE TABLE RAW.RAW_STOCK_PRICES;
