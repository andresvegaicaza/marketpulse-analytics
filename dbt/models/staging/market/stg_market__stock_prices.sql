with source as (

    select
        symbol,
        trade_date,
        open,
        high,
        low,
        close,
        volume,
        source,
        loaded_at
    from {{ source('market_raw', 'raw_stock_prices') }}

),

renamed as (

    select
        symbol                        as ticker_symbol,
        trade_date::date              as trading_date,
        open::number(18, 4)           as open_price,
        high::number(18, 4)           as high_price,
        low::number(18, 4)            as low_price,
        close::number(18, 4)          as close_price,
        volume::number(38, 0)         as volume,
        source                        as data_source,
        loaded_at
    from source

),

deduplicated as (

    select
        ticker_symbol,
        trading_date,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        data_source,
        loaded_at,
        row_number() over (
            partition by ticker_symbol, trading_date
            order by loaded_at desc
        ) as row_num
    from renamed

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
        data_source,
        loaded_at
    from deduplicated
    where row_num = 1

)

select * from final
