"""Snowflake connection and WATCHLIST CRUD operations for the Streamlit app."""

import os
from pathlib import Path
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _load_private_key():
    key_path = PROJECT_ROOT / os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "rsa_key.p8")
    return load_pem_private_key(key_path.read_bytes(), password=None)


def get_connection():
    """Return an open Snowflake connection using key-pair auth."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=_load_private_key(),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="APP",
    )


def get_all_tickers(conn) -> pd.DataFrame:
    """Return all tickers (active and inactive) as a DataFrame."""
    sql = """
        select
            symbol,
            company_name,
            category,
            notes,
            is_active,
            created_at,
            updated_at
        from APP.WATCHLIST
        order by is_active desc, symbol asc
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [col[0].lower() for col in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def add_ticker(conn, symbol: str, company_name: str, category: str, notes: str) -> str:
    """
    Add a new ticker or reactivate a deactivated one.
    Returns a status message describing what happened.
    """
    symbol = symbol.upper().strip()
    cursor = conn.cursor()

    cursor.execute(
        "select is_active from APP.WATCHLIST where symbol = %s",
        (symbol,)
    )
    existing = cursor.fetchone()

    if existing is None:
        cursor.execute(
            """
            insert into APP.WATCHLIST (symbol, company_name, category, notes)
            values (%s, %s, %s, %s)
            """,
            (symbol, company_name or None, category or None, notes or None)
        )
        conn.commit()
        return f"Added {symbol} to the watchlist."

    elif not existing[0]:
        cursor.execute(
            """
            update APP.WATCHLIST
            set
                is_active    = true,
                company_name = %s,
                category     = %s,
                notes        = %s,
                updated_at   = current_timestamp()
            where symbol = %s
            """,
            (company_name or None, category or None, notes or None, symbol)
        )
        conn.commit()
        return f"Reactivated {symbol} — it was previously deactivated."

    else:
        return f"{symbol} is already in your active watchlist."


def deactivate_ticker(conn, symbol: str) -> str:
    """Soft-delete a ticker by setting is_active = false."""
    cursor = conn.cursor()
    cursor.execute(
        """
        update APP.WATCHLIST
        set is_active = false, updated_at = current_timestamp()
        where symbol = %s and is_active = true
        """,
        (symbol,)
    )
    conn.commit()
    affected = cursor.rowcount
    if affected:
        return f"Deactivated {symbol}."
    return f"{symbol} was already inactive."


def reactivate_ticker(conn, symbol: str) -> str:
    """Reactivate a soft-deleted ticker."""
    cursor = conn.cursor()
    cursor.execute(
        """
        update APP.WATCHLIST
        set is_active = true, updated_at = current_timestamp()
        where symbol = %s and is_active = false
        """,
        (symbol,)
    )
    conn.commit()
    affected = cursor.rowcount
    if affected:
        return f"Reactivated {symbol}."
    return f"{symbol} was already active."


def update_ticker(conn, symbol: str, company_name: str, category: str, notes: str) -> str:
    """Update company name, category, and notes for an existing ticker."""
    cursor = conn.cursor()
    cursor.execute(
        """
        update APP.WATCHLIST
        set
            company_name = %s,
            category     = %s,
            notes        = %s,
            updated_at   = current_timestamp()
        where symbol = %s
        """,
        (company_name or None, category or None, notes or None, symbol)
    )
    conn.commit()
    return f"Updated {symbol}."
