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
    get_active_symbols,
    get_ticker_history,
    get_performance_summary,
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

tab_watchlist, tab_add, tab_manage, tab_analytics = st.tabs(["Watchlist", "Add Ticker", "Manage Ticker", "Analytics"])

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

# ── Tab 4: Analytics ──────────────────────────────────────────────────────────
with tab_analytics:
    st.subheader("Ticker Analytics")

    active_symbols = get_active_symbols(conn)
    if not active_symbols:
        st.info("No active tickers in your watchlist.")
    else:
        col_sym, col_period, col_bench = st.columns([2, 2, 2])
        with col_sym:
            ticker = st.selectbox("Ticker", active_symbols, key="analytics_ticker")
        with col_period:
            period = st.selectbox("Period", ["30D", "90D", "YTD", "1Y", "ALL_AVAILABLE"], index=1)
        with col_bench:
            benchmark = st.selectbox(
                "Benchmark",
                [s for s in active_symbols if s != ticker] if len(active_symbols) > 1 else ["SPY"],
                index=0
            )

        df = get_ticker_history(conn, ticker, period)

        if df.empty:
            st.warning(f"No data available for {ticker} in this period.")
        else:
            latest      = df.iloc[-1]
            first_close = df.iloc[0]["close_price"]
            last_close  = latest["close_price"]

            # ── Key metrics ──
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Current Price", f"${last_close:,.2f}",
                      f"{latest['daily_return_pct'] * 100:+.2f}% today" if latest["daily_return_pct"] else "—")
            period_ret = (last_close - first_close) / first_close * 100
            m2.metric("Period Return", f"{period_ret:+.2f}%")
            ann_vol = latest["annualized_volatility_20d"]
            m3.metric("Annualized Volatility", f"{ann_vol * 100:.1f}%" if ann_vol else "—")
            m4.metric("Avg Daily Volume", f"{df['volume'].mean():,.0f}")

            st.divider()

            # ── Signal flags ──
            flags = []
            if latest["close_price"] and latest["moving_average_20d"]:
                if latest["close_price"] > latest["moving_average_20d"]:
                    flags.append("🟢 Price is **above** the 20-day MA — bullish signal")
                else:
                    flags.append("🔴 Price is **below** the 20-day MA — bearish signal")
            if ann_vol and ann_vol > 0.30:
                flags.append(f"⚠️ High volatility — annualized vol at **{ann_vol * 100:.1f}%**")
            if latest["daily_return_pct"] and abs(latest["daily_return_pct"]) > 0.03:
                flags.append(f"⚡ Unusual move today: **{latest['daily_return_pct'] * 100:+.2f}%**")

            if flags:
                st.markdown("**Signals**")
                for f in flags:
                    st.markdown(f"- {f}")
                st.divider()

            # ── Price chart with moving averages ──
            st.markdown("**Price History & Moving Averages**")
            chart_df = df.set_index("trading_date")[
                ["close_price", "moving_average_7d", "moving_average_20d", "moving_average_50d"]
            ].rename(columns={
                "close_price":        "Close",
                "moving_average_7d":  "MA 7d",
                "moving_average_20d": "MA 20d",
                "moving_average_50d": "MA 50d",
            })
            st.line_chart(chart_df, height=320)

            # ── Benchmark comparison ──
            st.markdown(f"**Cumulative Return: {ticker} vs {benchmark}**")
            df_bench = get_ticker_history(conn, benchmark, period)
            if not df_bench.empty:
                t_base  = df["close_price"].iloc[0]
                b_base  = df_bench["close_price"].iloc[0]
                t_cum   = ((df.set_index("trading_date")["close_price"] / t_base) - 1) * 100
                b_cum   = ((df_bench.set_index("trading_date")["close_price"] / b_base) - 1) * 100
                cmp_df  = pd.concat([t_cum.rename(ticker), b_cum.rename(benchmark)], axis=1).dropna()
                st.line_chart(cmp_df, height=280)

            # ── $10k scenario ──
            st.markdown("**Scenario: $10,000 invested at period start**")
            shares      = 10_000 / first_close
            end_value   = shares * last_close
            gain_loss   = end_value - 10_000
            s1, s2, s3  = st.columns(3)
            s1.metric("Starting Value",  "$10,000.00")
            s2.metric("Current Value",   f"${end_value:,.2f}", f"{gain_loss:+,.2f}")
            s3.metric("Shares Acquired", f"{shares:.4f} shares @ ${first_close:.2f}")

            st.divider()

            # ── Period performance summary table ──
            st.markdown("**Performance Summary by Period**")
            summary = get_performance_summary(conn, ticker)
            if not summary.empty:
                summary["period_return_pct"]    = (summary["period_return_pct"]    * 100).map("{:+.2f}%".format)
                summary["avg_daily_return_pct"] = (summary["avg_daily_return_pct"] * 100).map("{:+.4f}%".format)
                summary["volatility_pct"]       = (summary["volatility_pct"]       * 100).map("{:.2f}%".format)
                summary["start_close_price"]    = summary["start_close_price"].map("${:,.2f}".format)
                summary["end_close_price"]      = summary["end_close_price"].map("${:,.2f}".format)
                summary["avg_volume"]           = summary["avg_volume"].map("{:,.0f}".format)
                st.dataframe(
                    summary.rename(columns={
                        "period_name":         "Period",
                        "period_start_date":   "Start",
                        "period_end_date":     "End",
                        "start_close_price":   "Start Price",
                        "end_close_price":     "End Price",
                        "period_return_pct":   "Total Return",
                        "avg_daily_return_pct":"Avg Daily Return",
                        "volatility_pct":      "Volatility",
                        "min_close_price":     "Min Price",
                        "max_close_price":     "Max Price",
                        "avg_volume":          "Avg Volume",
                        "trading_days_count":  "Trading Days",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
