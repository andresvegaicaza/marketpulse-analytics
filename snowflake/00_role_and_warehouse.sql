-- Run this as ACCOUNTADMIN in a Snowflake worksheet
-- Creates the role, warehouse, and assigns key-pair auth to your user

USE ROLE ACCOUNTADMIN;

-- 1. Create a dedicated warehouse
CREATE WAREHOUSE IF NOT EXISTS MARKETPULSE_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    COMMENT = 'MarketPulse Analytics warehouse';

-- 2. Create a dedicated role
CREATE ROLE IF NOT EXISTS MARKETPULSE_ROLE;

-- 3. Grant warehouse usage to the role
GRANT USAGE ON WAREHOUSE MARKETPULSE_WH TO ROLE MARKETPULSE_ROLE;

-- 4. Assign the role to your user
GRANT ROLE MARKETPULSE_ROLE TO USER AVEGAICAZA;

-- 5. Assign your RSA public key to your user for key-pair auth
--    Paste the public key body below (no header/footer lines)
ALTER USER AVEGAICAZA SET RSA_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0cttkIrwdtfFpSRrIRbPHc4TqJ8GWPPGfw2oVHLG+pBuvGxoSMLYCMJzmab+tAodrt1WK1epY79HpeEnB4QPFy69BY46Rr1BVEgQg59KPDQkGA1tySpMZwKvBT4NQczo9oUqsK0bnv0ZM+QJ5X+ot7yIWMPmYvmCTPommyXWLa08p/X0vZQvFjHqQxKDWBuTf8LlpkAg78DQ6r+Fy6sti3SbHRWFXrQByhzvRgd73rJcZ+UZkmRtZMX5fNdb20rrCELT3o2C0tXKjr2GASu2h5vWumgZ3C3VJxRTc7XK+vdawvCcc9lnFJembmBVs3cKnsUnw0o0suDyfjkZwjZw+wIDAQAB';

-- 6. Verify key was set
DESC USER AVEGAICAZA;
