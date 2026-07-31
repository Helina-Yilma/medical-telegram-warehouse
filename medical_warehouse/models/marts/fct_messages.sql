with stg_messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

final as (
    select
        m.message_id,
        -- Apply trim and lower to ensure the hash matches dim_channels perfectly
        md5(trim(lower(m.channel_name))) as channel_key, 
        to_char(m.message_at, 'YYYYMMDD')::integer as date_key, 

        m.message_text,
        m.message_length,
        m.view_count,
        m.forward_count,
        m.has_image
    from stg_messages m
)

select * from final