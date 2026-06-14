with date_spine as (

    -- Generate every calendar date from 2024-01-01 to 2027-12-31 (1461 days)
    select dateadd(day, seq4(), '2024-01-01'::date) as date_day
    from table(generator(rowcount => 1461))

),

market_holidays as (

    select
        holiday_date,
        holiday_name
    from {{ ref('market_holidays') }}
    where market_code = 'NYSE'
        and is_full_day_closure = true

),

with_attributes as (

    select
        d.date_day,
        to_number(to_char(d.date_day, 'YYYYMMDD'))         as date_key,
        year(d.date_day)                                    as calendar_year,
        quarter(d.date_day)                                 as calendar_quarter,
        month(d.date_day)                                   as calendar_month,
        to_char(d.date_day, 'MMMM')                        as calendar_month_name,
        monthname(d.date_day)                               as calendar_month_short_name,
        weekofyear(d.date_day)                              as calendar_week,
        day(d.date_day)                                     as day_of_month,
        dayofweekiso(d.date_day)                            as day_of_week,
        to_char(d.date_day, 'DDDD')                        as day_of_week_name,
        dayname(d.date_day)                                 as day_of_week_short_name,
        dayofyear(d.date_day)                               as day_of_year,
        date_trunc('week', d.date_day)                      as week_start_date,
        dateadd(day, 6, date_trunc('week', d.date_day))     as week_end_date,
        date_trunc('month', d.date_day)                     as month_start_date,
        last_day(d.date_day)                                as month_end_date,
        date_trunc('quarter', d.date_day)                   as quarter_start_date,
        last_day(d.date_day, 'quarter')                     as quarter_end_date,
        date_trunc('year', d.date_day)                      as year_start_date,
        last_day(d.date_day, 'year')                        as year_end_date,
        case when dayofweekiso(d.date_day) in (6, 7)
            then true else false end                        as is_weekend,
        case when dayofweekiso(d.date_day) not in (6, 7)
            then true else false end                        as is_weekday,
        case when h.holiday_date is not null
            then true else false end                        as is_market_holiday,
        h.holiday_name                                      as market_holiday_name,
        case
            when dayofweekiso(d.date_day) not in (6, 7)
                and h.holiday_date is null
            then true else false
        end                                                 as is_trading_day
    from date_spine as d
    left join market_holidays as h
        on d.date_day = h.holiday_date

),

with_trading_dates as (

    select
        *,
        lag(case when is_trading_day then date_day end) ignore nulls
            over (order by date_day)                        as previous_trading_date,
        lead(case when is_trading_day then date_day end) ignore nulls
            over (order by date_day)                        as next_trading_date
    from with_attributes

),

with_trading_counters as (

    select
        *,
        sum(case when is_trading_day then 1 else 0 end)
            over (
                partition by calendar_year, calendar_month
                order by date_day
                rows between unbounded preceding and current row
            )                                               as trading_day_of_month,
        sum(case when is_trading_day then 1 else 0 end)
            over (
                partition by calendar_year
                order by date_day
                rows between unbounded preceding and current row
            )                                               as trading_day_of_year
    from with_trading_dates

),

final as (

    select
        date_key,
        date_day,
        calendar_year,
        calendar_quarter,
        calendar_month,
        calendar_month_name,
        calendar_month_short_name,
        calendar_week,
        day_of_month,
        day_of_week,
        day_of_week_name,
        day_of_week_short_name,
        day_of_year,
        week_start_date,
        week_end_date,
        month_start_date,
        month_end_date,
        quarter_start_date,
        quarter_end_date,
        year_start_date,
        year_end_date,
        is_weekend,
        is_weekday,
        is_market_holiday,
        market_holiday_name,
        is_trading_day,
        previous_trading_date,
        next_trading_date,
        trading_day_of_month,
        trading_day_of_year
    from with_trading_counters

)

select * from final
