{{ config(materialized='table') }}

WITH yolo_raw AS (
    -- Get the detections you just loaded via Python
    SELECT 
        message_id,
        detected_objects AS detected_class,
        confidence_score,
        image_category
    FROM {{ source('raw_data', 'yolo_detections') }}
),

core_messages AS (
    -- Get the keys from your existing fact table
    SELECT 
        message_id,
        channel_key,
        date_key
    FROM {{ ref('fct_messages') }}
)

SELECT 
    m.message_id,
    m.channel_key,
    m.date_key,
    y.detected_class,
    y.confidence_score,
    y.image_category
FROM core_messages m
INNER JOIN yolo_raw y ON m.message_id = y.message_id