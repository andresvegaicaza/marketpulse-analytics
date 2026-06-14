"""Snowflake connection and data access helpers."""

import os
from pathlib import Path
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv
import snowflake.connector

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _load_private_key():
    key_path = PROJECT_ROOT / os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "rsa_key.p8")
    key_bytes = key_path.read_bytes()
    return load_pem_private_key(key_bytes, password=None)


def get_connection():
    """Return an open Snowflake connection using key-pair auth."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=_load_private_key(),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def get_active_tickers(conn):
    """Return a list of active ticker symbols from APP.WATCHLIST."""
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM APP.WATCHLIST WHERE is_active = TRUE")
    return [row[0] for row in cursor.fetchall()]


def insert_prices(conn, rows):
    """Insert a list of price rows into RAW.RAW_STOCK_PRICES.

    Each row is a tuple: (symbol, trade_date, open, high, low, close, volume, source)
    """
    sql = """
        INSERT INTO RAW.RAW_STOCK_PRICES
            (symbol, trade_date, open, high, low, close, volume, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor = conn.cursor()
    cursor.executemany(sql, rows)
    conn.commit()
    return cursor.rowcount
