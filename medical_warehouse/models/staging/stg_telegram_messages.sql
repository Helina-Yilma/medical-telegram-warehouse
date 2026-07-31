with source as (
    select * from {{ source('raw_data', 'telegram_messages') }}
),

staged as (
    select
        -- 1. Rename to consistent naming (snake_case)
        message_id,
        channel_name,
        channel_title,

        -- 2. Cast data types appropriately
        cast(message_date as timestamp) as message_at,
        cast(views as integer) as view_count,
        cast(forwards as integer) as forward_count,

        -- 3. Add calculated fields
        length(message_text) as message_length,
        case 
            when has_media = true then 1 
            else 0 
        end as has_image, -- flag as 1/0 or boolean

        -- Raw text and path
        message_text,
        image_path

    from source
    -- 4. Remove or filter invalid records
    where message_id is not null
      and message_text is not null
)

select * from staged