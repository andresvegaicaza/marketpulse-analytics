with tickers as (

    select
        ticker_id,
        ticker_symbol,
        company_name,
        category,
        notes,
        is_active,
        created_at,
        updated_at
    from {{ ref('stg_market__tickers') }}

),

final as (

    select
        ticker_id                   as ticker_key,
        ticker_symbol,
        company_name,

        -- Metadata not yet available in the watchlist source.
        -- Will be populated when M1 (Streamlit app) adds these fields.
        null::varchar               as asset_type,
        null::varchar               as exchange_code,
        null::varchar               as sector,
        null::varchar               as industry,
        'USD'::varchar              as currency,
        'US'::varchar               as country,

        category,
        notes,
        is_active,
        created_at                  as first_added_at,
        updated_at                  as last_updated_at
    from tickers

)

select * from final
