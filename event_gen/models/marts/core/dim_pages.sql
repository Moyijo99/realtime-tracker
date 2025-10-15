{{
  config(
    materialized='table'
  )
}}

with page_events as (
    select
        page_url,
        domain,
        page_path,
        count(*) as total_events,
        count(distinct user_id) as unique_visitors,
        count(distinct case when event_type = 'page_view' then event_id end) as page_views,
        count(distinct case when event_type = 'click' then event_id end) as clicks,
        min(event_timestamp) as first_visit,
        max(event_timestamp) as last_visit
    from {{ ref('stg_events') }}
    group by page_url, domain, page_path
)

select
    {{ dbt_utils.generate_surrogate_key(['page_url']) }} as page_key,
    page_url,
    domain,
    page_path,
    total_events,
    unique_visitors,
    page_views,
    clicks,
    first_visit,
    last_visit,
    round(clicks / nullif(page_views, 0) * 100, 2) as click_through_rate,
    current_timestamp() as updated_at
from page_events
