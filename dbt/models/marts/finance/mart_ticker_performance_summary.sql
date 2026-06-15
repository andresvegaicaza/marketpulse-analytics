with performance as (

    select
        ticker_symbol,
        trading_date,
        close_price,
        daily_return_pct,
        volatility_20d
    from {{ ref('fact_stock_performance_daily') }}

),

prices as (

    select
        ticker_symbol,
        trading_date,
        volume
    from {{ ref('fact_stock_price_daily') }}

),

tickers as (

    select
        ticker_key,
        ticker_symbol,
        company_name,
        category
    from {{ ref('dim_ticker') }}

),

-- global date anchors computed once
anchors as (

    select
        max(trading_date)                               as latest_date,
        dateadd(day, -29, max(trading_date))            as start_30d,
        dateadd(day, -89, max(trading_date))            as start_90d,
        date_trunc('year', max(trading_date))           as start_ytd,
        date_trunc('month', max(trading_date))          as start_mtd,
        dateadd(year, -1, max(trading_date))            as start_1y,
        min(trading_date)                               as start_all
    from performance

),

-- 6 period definitions — no per-ticker duplication
period_defs as (

    select 'ALL_AVAILABLE'  as period_name, start_all    as period_start, latest_date as period_end from anchors
    union all
    select 'YTD',           start_ytd,   latest_date from anchors
    union all
    select 'MTD',           start_mtd,   latest_date from anchors
    union all
    select '30D',           start_30d,   latest_date from anchors
    union all
    select '90D',           start_90d,   latest_date from anchors
    union all
    select '1Y',            start_1y,    latest_date from anchors

),

-- for each ticker × period: aggregate metrics and capture actual boundary dates
ticker_periods as (

    select
        p.ticker_symbol,
        pd.period_name,
        pd.period_start                                 as nominal_period_start,
        pd.period_end                                   as period_end_date,
        min(p.trading_date)                             as actual_start_date,
        max(p.trading_date)                             as actual_end_date,
        count(p.trading_date)                           as trading_days_count,
        min(p.close_price)                              as min_close_price,
        max(p.close_price)                              as max_close_price,
        avg(p.daily_return_pct)                         as avg_daily_return_pct,
        avg(p.volatility_20d)                           as volatility_pct,
        avg(pr.volume)                                  as avg_volume
    from performance as p
    cross join period_defs as pd
    inner join prices as pr
        on p.ticker_symbol = pr.ticker_symbol
        and p.trading_date = pr.trading_date
    where p.trading_date between pd.period_start and pd.period_end
    group by
        p.ticker_symbol,
        pd.period_name,
        pd.period_start,
        pd.period_end

),

-- fetch actual start and end close prices by joining on boundary dates
final as (

    select
        tp.ticker_symbol,
        t.company_name,
        t.category,
        tp.period_name,
        tp.actual_start_date                            as period_start_date,
        tp.actual_end_date                              as period_end_date,
        p_start.close_price                             as start_close_price,
        p_end.close_price                               as end_close_price,
        {{ safe_divide(
            'p_end.close_price - p_start.close_price',
            'p_start.close_price'
        ) }}                                            as period_return_pct,
        tp.avg_daily_return_pct,
        tp.volatility_pct,
        tp.min_close_price,
        tp.max_close_price,
        tp.avg_volume,
        tp.trading_days_count
    from ticker_periods as tp
    inner join tickers as t
        on tp.ticker_symbol = t.ticker_symbol
    inner join performance as p_start
        on tp.ticker_symbol = p_start.ticker_symbol
        and tp.actual_start_date = p_start.trading_date
    inner join performance as p_end
        on tp.ticker_symbol = p_end.ticker_symbol
        and tp.actual_end_date = p_end.trading_date

)

select * from final
