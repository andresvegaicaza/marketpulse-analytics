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

-- Anchor dates for each period relative to the latest available trading date
period_anchors as (

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

-- One row per ticker per period using cross join
periods as (

    select ticker_symbol, 'ALL_AVAILABLE'  as period_name, a.start_all    as period_start, a.latest_date as period_end from performance cross join period_anchors as a group by 1, 2, 3, 4
    union all
    select ticker_symbol, 'YTD',           a.start_ytd,   a.latest_date from performance cross join period_anchors as a group by 1, 2, 3, 4
    union all
    select ticker_symbol, 'MTD',           a.start_mtd,   a.latest_date from performance cross join period_anchors as a group by 1, 2, 3, 4
    union all
    select ticker_symbol, '30D',           a.start_30d,   a.latest_date from performance cross join period_anchors as a group by 1, 2, 3, 4
    union all
    select ticker_symbol, '90D',           a.start_90d,   a.latest_date from performance cross join period_anchors as a group by 1, 2, 3, 4
    union all
    select ticker_symbol, '1Y',            a.start_1y,    a.latest_date from performance cross join period_anchors as a group by 1, 2, 3, 4

),

-- Aggregate metrics for each ticker-period combination
aggregated as (

    select
        pe.ticker_symbol,
        pe.period_name,
        pe.period_start                                 as period_start_date,
        pe.period_end                                   as period_end_date,
        count(p.trading_date)                           as trading_days_count,
        min(p.close_price)                              as min_close_price,
        max(p.close_price)                              as max_close_price,
        avg(p.daily_return_pct)                         as avg_daily_return_pct,
        avg(p.volatility_20d)                           as volatility_pct,
        sum(pr.volume)                                  as total_volume,
        avg(pr.volume)                                  as avg_volume
    from periods as pe
    inner join performance as p
        on pe.ticker_symbol = p.ticker_symbol
        and p.trading_date between pe.period_start and pe.period_end
    inner join prices as pr
        on p.ticker_symbol = pr.ticker_symbol
        and p.trading_date = pr.trading_date
    group by 1, 2, 3, 4

),

-- Get start and end close prices for period return calculation
period_prices as (

    select
        pe.ticker_symbol,
        pe.period_name,
        first_value(p.close_price) over (
            partition by pe.ticker_symbol, pe.period_name
            order by p.trading_date asc
        )                                               as start_close_price,
        last_value(p.close_price) over (
            partition by pe.ticker_symbol, pe.period_name
            order by p.trading_date asc
            rows between unbounded preceding and unbounded following
        )                                               as end_close_price
    from periods as pe
    inner join performance as p
        on pe.ticker_symbol = p.ticker_symbol
        and p.trading_date between pe.period_start and pe.period_end

),

period_prices_deduped as (

    select distinct
        ticker_symbol,
        period_name,
        start_close_price,
        end_close_price
    from period_prices

),

final as (

    select
        a.ticker_symbol,
        t.company_name,
        t.category,
        a.period_name,
        a.period_start_date,
        a.period_end_date,
        pp.start_close_price,
        pp.end_close_price,
        {{ safe_divide('pp.end_close_price - pp.start_close_price',
                       'pp.start_close_price') }}       as period_return_pct,
        a.avg_daily_return_pct,
        a.volatility_pct,
        a.min_close_price,
        a.max_close_price,
        a.total_volume,
        a.avg_volume,
        a.trading_days_count
    from aggregated as a
    inner join tickers as t
        on a.ticker_symbol = t.ticker_symbol
    inner join period_prices_deduped as pp
        on a.ticker_symbol = pp.ticker_symbol
        and a.period_name = pp.period_name

)

select * from final
