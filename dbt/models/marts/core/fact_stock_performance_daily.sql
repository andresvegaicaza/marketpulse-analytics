with daily_returns as (

    select
        ticker_symbol,
        trading_date,
        close_price,
        previous_close_price,
        price_change,
        daily_return_pct
    from {{ ref('int_stock_daily_returns') }}

),

moving_averages as (

    select
        ticker_symbol,
        trading_date,
        moving_average_7d,
        moving_average_20d,
        moving_average_50d
    from {{ ref('int_stock_moving_averages') }}

),

volatility as (

    select
        ticker_symbol,
        trading_date,
        volatility_20d,
        annualized_volatility_20d
    from {{ ref('int_stock_volatility') }}

),

dim_date as (

    select
        date_key,
        date_day
    from {{ ref('dim_date') }}

),

dim_ticker as (

    select
        ticker_key,
        ticker_symbol
    from {{ ref('dim_ticker') }}

),

joined as (

    select
        r.ticker_symbol,
        r.trading_date,
        r.close_price,
        r.previous_close_price,
        r.price_change,
        r.daily_return_pct,
        ma.moving_average_7d,
        ma.moving_average_20d,
        ma.moving_average_50d,
        v.volatility_20d,
        v.annualized_volatility_20d
    from daily_returns as r
    inner join moving_averages as ma
        on r.ticker_symbol = ma.ticker_symbol
        and r.trading_date = ma.trading_date
    inner join volatility as v
        on r.ticker_symbol = v.ticker_symbol
        and r.trading_date = v.trading_date

),

final as (

    select
        j.ticker_symbol,
        dt.ticker_key,
        dd.date_key,
        j.trading_date,
        j.close_price,
        j.previous_close_price,
        j.price_change,
        j.daily_return_pct,
        j.moving_average_7d,
        j.moving_average_20d,
        j.moving_average_50d,
        j.volatility_20d,
        j.annualized_volatility_20d
    from joined as j
    inner join dim_date as dd
        on j.trading_date = dd.date_day
    inner join dim_ticker as dt
        on j.ticker_symbol = dt.ticker_symbol

)

select * from final
