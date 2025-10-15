{{
  config(
    materialized='table'
  )
}}

with user_events as (
    select
        user_id,
        username,
        min(event_timestamp) as first_event_at,
        max(event_timestamp) as last_event_at,
        count(*) as total_events,
        count(distinct event_date) as days_active,
        count(distinct case when event_type = 'page_view' then event_id end) as page_views,
        count(distinct case when event_type = 'click' then event_id end) as clicks,
        count(distinct page_url) as unique_pages_visited
    from {{ ref('stg_events') }}
    group by user_id, username
)

select
    {{ dbt_utils.generate_surrogate_key(['user_id']) }} as user_key,
    user_id,
    username,
    first_event_at,
    last_event_at,
    total_events,
    days_active,
    page_views,
    clicks,
    unique_pages_visited,
    round(total_events / nullif(days_active, 0), 2) as avg_events_per_day,
    current_timestamp() as updated_at
from user_events
