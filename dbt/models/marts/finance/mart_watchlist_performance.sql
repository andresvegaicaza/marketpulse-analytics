with performance as (

    select
        ticker_symbol,
        ticker_key,
        date_key,
        trading_date,
        close_price,
        previous_close_price,
        daily_return_pct,
        moving_average_7d,
        moving_average_20d,
        moving_average_50d,
        volatility_20d,
        annualized_volatility_20d
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
        category,
        currency,
        country,
        is_active
    from {{ ref('dim_ticker') }}

),

dates as (

    select
        date_key,
        date_day,
        calendar_year,
        calendar_quarter,
        calendar_month,
        calendar_month_name
    from {{ ref('dim_date') }}

),

final as (

    select
        t.ticker_symbol,
        t.company_name,
        t.category,
        t.currency,
        t.country,
        t.is_active,
        d.date_day                      as trading_date,
        d.calendar_year,
        d.calendar_quarter,
        d.calendar_month,
        d.calendar_month_name,
        p.close_price,
        p.previous_close_price,
        p.daily_return_pct,
        p.moving_average_7d,
        p.moving_average_20d,
        p.moving_average_50d,
        p.volatility_20d,
        p.annualized_volatility_20d,
        pr.volume
    from performance as p
    inner join tickers as t
        on p.ticker_symbol = t.ticker_symbol
    inner join dates as d
        on p.date_key = d.date_key
    inner join prices as pr
        on p.ticker_symbol = pr.ticker_symbol
        and p.trading_date = pr.trading_date
    where t.is_active = true

)

select * from final
