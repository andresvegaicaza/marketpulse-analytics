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


def get_active_symbols(conn) -> list[str]:
    """Return list of active ticker symbols."""
    cursor = conn.cursor()
    cursor.execute("select symbol from APP.WATCHLIST where is_active = true order by symbol")
    return [row[0] for row in cursor.fetchall()]


def get_ticker_history(conn, symbol: str, period: str = "ALL_AVAILABLE") -> pd.DataFrame:
    """Return price history with moving averages for a ticker from the mart."""
    period_filter = {
        "30D":           "dateadd(day, -29, (select max(trading_date) from MARKETPULSE_DEV.MARTS.mart_watchlist_performance))",
        "90D":           "dateadd(day, -89, (select max(trading_date) from MARKETPULSE_DEV.MARTS.mart_watchlist_performance))",
        "YTD":           "date_trunc('year', (select max(trading_date) from MARKETPULSE_DEV.MARTS.mart_watchlist_performance))",
        "1Y":            "dateadd(year, -1, (select max(trading_date) from MARKETPULSE_DEV.MARTS.mart_watchlist_performance))",
        "ALL_AVAILABLE": "to_date('1900-01-01')",
    }
    start_expr = period_filter.get(period, "to_date('1900-01-01')")

    sql = f"""
        select
            trading_date,
            close_price,
            moving_average_7d,
            moving_average_20d,
            moving_average_50d,
            daily_return_pct,
            volume,
            volatility_20d,
            annualized_volatility_20d
        from MARKETPULSE_DEV.MARTS.mart_watchlist_performance
        where ticker_symbol = %s
          and trading_date >= {start_expr}
        order by trading_date asc
    """
    cursor = conn.cursor()
    cursor.execute(sql, (symbol,))
    rows = cursor.fetchall()
    cols = [c[0].lower() for c in cursor.description]
    df = pd.DataFrame(rows, columns=cols)
    for col in cols:
        if col != "trading_date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_performance_summary(conn, symbol: str) -> pd.DataFrame:
    """Return period performance summary for a ticker."""
    sql = """
        select
            period_name,
            period_start_date,
            period_end_date,
            start_close_price,
            end_close_price,
            period_return_pct,
            avg_daily_return_pct,
            volatility_pct,
            min_close_price,
            max_close_price,
            avg_volume,
            trading_days_count
        from MARKETPULSE_DEV.MARTS.mart_ticker_performance_summary
        where ticker_symbol = %s
        order by
            case period_name
                when 'MTD'           then 1
                when '30D'           then 2
                when '90D'           then 3
                when 'YTD'           then 4
                when '1Y'            then 5
                when 'ALL_AVAILABLE' then 6
            end
    """
    cursor = conn.cursor()
    cursor.execute(sql, (symbol,))
    rows = cursor.fetchall()
    cols = [c[0].lower() for c in cursor.description]
    df = pd.DataFrame(rows, columns=cols)
    for col in cols:
        if col not in ("ticker_symbol", "company_name", "category", "period_name", "period_start_date", "period_end_date"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
