with returns as (

    select
        ticker_symbol,
        trading_date,
        daily_return_pct
    from {{ ref('int_stock_daily_returns') }}

),

final as (

    select
        ticker_symbol,
        trading_date,
        daily_return_pct,

        stddev(daily_return_pct) over (
            partition by ticker_symbol
            order by trading_date
            rows between 19 preceding and current row
        ) as volatility_20d,

        stddev(daily_return_pct) over (
            partition by ticker_symbol
            order by trading_date
            rows between 19 preceding and current row
        ) * sqrt(252)                                                   as annualized_volatility_20d

    from returns

)

select * from final
