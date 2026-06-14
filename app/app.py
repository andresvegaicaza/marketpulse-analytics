"""MarketPulse — Watchlist Manager Streamlit app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from db import (
    get_connection,
    get_all_tickers,
    add_ticker,
    deactivate_ticker,
    reactivate_ticker,
    update_ticker,
)

st.set_page_config(
    page_title="MarketPulse — Watchlist",
    page_icon="📈",
    layout="wide",
)

st.title("📈 MarketPulse — Watchlist Manager")
st.caption("Manage your stock watchlist. Analytics live in Power BI.")

CATEGORIES = ["", "Tech", "Finance", "ETF", "Energy", "Healthcare", "Consumer", "Space", "Other"]


@st.cache_resource
def get_conn():
    return get_connection()


conn = get_conn()

tab_watchlist, tab_add, tab_manage = st.tabs(["Watchlist", "Add Ticker", "Manage Ticker"])

# ── Tab 1: Watchlist ──────────────────────────────────────────────────────────
with tab_watchlist:
    st.subheader("Your Watchlist")

    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        show_inactive = st.checkbox("Show inactive tickers", value=False)
    with col_filter2:
        if st.button("Refresh", key="refresh_watchlist"):
            st.cache_data.clear()

    df = get_all_tickers(conn)

    if not show_inactive:
        df = df[df["is_active"] == True]

    if df.empty:
        st.info("No tickers in your watchlist yet. Use the Add Ticker tab to get started.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "symbol":       st.column_config.TextColumn("Symbol"),
                "company_name": st.column_config.TextColumn("Company"),
                "category":     st.column_config.TextColumn("Category"),
                "notes":        st.column_config.TextColumn("Notes"),
                "is_active":    st.column_config.CheckboxColumn("Active"),
                "created_at":   st.column_config.DatetimeColumn("Added", format="YYYY-MM-DD HH:mm"),
                "updated_at":   st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm"),
            },
            hide_index=True,
        )
        st.caption(f"{len(df)} ticker(s) shown.")

# ── Tab 2: Add Ticker ─────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Add a Ticker")
    st.info("Re-adding a previously deactivated ticker will reactivate it.")

    with st.form("form_add_ticker", clear_on_submit=True):
        symbol_input = st.text_input("Ticker Symbol *", placeholder="e.g. NVDA").upper().strip()
        company_input = st.text_input("Company Name", placeholder="e.g. NVIDIA Corporation")
        category_input = st.selectbox("Category", CATEGORIES)
        notes_input = st.text_area("Notes", placeholder="Optional notes about this ticker")
        submitted = st.form_submit_button("Add Ticker", type="primary")

    if submitted:
        if not symbol_input:
            st.error("Ticker symbol is required.")
        else:
            message = add_ticker(conn, symbol_input, company_input, category_input, notes_input)
            st.success(message)

# ── Tab 3: Manage Ticker ──────────────────────────────────────────────────────
with tab_manage:
    st.subheader("Manage a Ticker")

    df_all = get_all_tickers(conn)

    if df_all.empty:
        st.info("No tickers to manage yet.")
    else:
        selected_symbol = st.selectbox(
            "Select a ticker",
            options=df_all["symbol"].tolist(),
            format_func=lambda s: f"{s}  ({'Active' if df_all[df_all['symbol'] == s]['is_active'].values[0] else 'Inactive'})"
        )

        row = df_all[df_all["symbol"] == selected_symbol].iloc[0]
        is_active = bool(row["is_active"])

        st.divider()

        # ── Edit section ──
        st.markdown("**Edit details**")
        with st.form("form_edit_ticker"):
            edit_company = st.text_input("Company Name", value=row["company_name"] or "")
            edit_category = st.selectbox(
                "Category",
                CATEGORIES,
                index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else 0
            )
            edit_notes = st.text_area("Notes", value=row["notes"] or "")
            save = st.form_submit_button("Save Changes", type="primary")

        if save:
            msg = update_ticker(conn, selected_symbol, edit_company, edit_category, edit_notes)
            st.success(msg)

        st.divider()

        # ── Activate / Deactivate section ──
        st.markdown("**Status**")
        if is_active:
            st.write(f"**{selected_symbol}** is currently **active**.")
            if st.button(f"Deactivate {selected_symbol}", type="secondary"):
                msg = deactivate_ticker(conn, selected_symbol)
                st.warning(msg)
        else:
            st.write(f"**{selected_symbol}** is currently **inactive**.")
            if st.button(f"Reactivate {selected_symbol}", type="primary"):
                msg = reactivate_ticker(conn, selected_symbol)
                st.success(msg)
