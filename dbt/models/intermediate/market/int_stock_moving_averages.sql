with prices as (

    select
        ticker_symbol,
        trading_date,
        close_price
    from {{ ref('stg_market__stock_prices') }}

),

final as (

    select
        ticker_symbol,
        trading_date,
        close_price,

        avg(close_price) over (
            partition by ticker_symbol
            order by trading_date
            rows between 6 preceding and current row
        ) as moving_average_7d,

        avg(close_price) over (
            partition by ticker_symbol
            order by trading_date
            rows between 19 preceding and current row
        ) as moving_average_20d,

        avg(close_price) over (
            partition by ticker_symbol
            order by trading_date
            rows between 49 preceding and current row
        ) as moving_average_50d

    from prices

)

select * from final
