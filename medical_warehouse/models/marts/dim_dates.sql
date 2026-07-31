with range_values as (
    -- Find the start and end dates from your actual data
    select
        min(message_at)::date as start_date,
        max(message_at)::date as end_date
    from {{ ref('stg_telegram_messages') }}
),

date_series as (
    -- Generate every day between that min and max
    select generate_series(
        (select start_date from range_values),
        (select end_date from range_values),
        '1 day'::interval
    )::date as full_date
),

staged as (
    select
        to_char(full_date, 'YYYYMMDD')::integer as date_key,
        full_date,
        extract(dow from full_date) as day_of_week,
        to_char(full_date, 'Day') as day_name,
        extract(week from full_date) as week_of_year,
        extract(month from full_date) as month,
        to_char(full_date, 'Month') as month_name,
        extract(quarter from full_date) as quarter,
        extract(year from full_date) as year,
        case 
            when extract(dow from full_date) in (0, 6) then true 
            else false 
        end as is_weekend
    from date_series
)

select * from staged