{{
  config(
    materialized='view',
    engine='MergeTree()',
    order_by='(event_timestamp, user_id)'
  )
}}

with source_events as (
    select
        event_id,
        user_id,
        username,
        event_type,
        page_url,
        ip_address,
        timestamp
    from {{ source('raw', 'events') }}
),

cleaned_events as (
    select
        trim(event_id) as event_id,
        trim(user_id) as user_id,
        trim(lower(username)) as username,
        trim(lower(event_type)) as event_type,
        trim(page_url) as page_url,
        trim(ip_address) as ip_address,
        timestamp as event_timestamp,
        toDate(timestamp) as event_date,
        toHour(timestamp) as event_hour,
        toDayOfWeek(timestamp) as day_of_week,
        splitByChar('/', page_url)[3] as domain,
        splitByChar('?', page_url)[1] as page_path
        
    from source_events
    where event_id != ''
      and user_id != ''
      and timestamp is not null
)

select * from cleaned_events