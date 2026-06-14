with source as (

    select
        watchlist_id,
        symbol,
        company_name,
        category,
        notes,
        is_active,
        created_at,
        updated_at
    from {{ source('market_app', 'watchlist') }}

),

renamed as (

    select
        watchlist_id                  as ticker_id,
        upper(symbol)                 as ticker_symbol,
        company_name,
        category,
        notes,
        is_active,
        created_at,
        updated_at
    from source

),

final as (

    select
        ticker_id,
        ticker_symbol,
        company_name,
        category,
        notes,
        is_active,
        created_at,
        updated_at
    from renamed

)

select * from final
