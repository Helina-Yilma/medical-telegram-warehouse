with stg_data as (
    select * from {{ ref('stg_telegram_messages') }}
),

channel_summary as (
    select
        -- Exact same logic as fct_messages
        md5(trim(lower(channel_name))) as channel_key,
        trim(channel_name) as channel_name,
        -- Categorization logic
        case 
            when channel_name ilike '%pharm%' then 'Pharmaceutical'
            when channel_name ilike '%cosmetic%' then 'Cosmetics'
            else 'Medical' 
        end as channel_type,
        min(message_at) as first_post_date,
        max(message_at) as last_post_date,
        count(message_id) as total_posts,
        avg(view_count) as avg_views
    from stg_data
    group by 1, 2, 3
)

select * from channel_summary