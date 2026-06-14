with prices as (

    select
        ticker_symbol,
        trading_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume
    from {{ ref('stg_market__stock_prices') }}

),

with_prev_close as (

    select
        ticker_symbol,
        trading_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        lag(close_price) over (
            partition by ticker_symbol
            order by trading_date
        ) as previous_close_price
    from prices

),

final as (

    select
        ticker_symbol,
        trading_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        previous_close_price,
        close_price - previous_close_price                              as price_change,
        {{ safe_divide('close_price - previous_close_price',
                       'previous_close_price') }}                       as daily_return_pct
    from with_prev_close

)

select * from final
