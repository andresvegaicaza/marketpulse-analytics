with stock_prices as (

    select
        ticker_symbol,
        trading_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        data_source,
        loaded_at
    from {{ ref('stg_market__stock_prices') }}

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

final as (

    select
        sp.ticker_symbol,
        dt.ticker_key,
        dd.date_key,
        sp.trading_date,
        sp.open_price,
        sp.high_price,
        sp.low_price,
        sp.close_price,
        sp.volume,
        sp.data_source,
        sp.loaded_at
    from stock_prices as sp
    inner join dim_date as dd
        on sp.trading_date = dd.date_day
    inner join dim_ticker as dt
        on sp.ticker_symbol = dt.ticker_symbol

)

select * from final
