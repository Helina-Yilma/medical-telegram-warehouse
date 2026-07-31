select
    message_id,
    message_at
from {{ ref('stg_telegram_messages') }}
where message_at > now()