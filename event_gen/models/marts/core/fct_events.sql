{{
  config(
    materialized='table',
    engine='MergeTree()',
    order_by='(event_timestamp, event_key)'
  )
}}

select
    event_id as event_key,
    user_id,
    username,
    event_type,
    page_url,
    ip_address,
    event_timestamp,
    event_date,
    event_hour,
    day_of_week,
    1 as event_count,
    now() as loaded_at
from {{ ref('stg_events') }}
