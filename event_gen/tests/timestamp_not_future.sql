-- Test to ensure event timestamps are not in the future
-- This test will fail if any events have timestamps after current time

select
    event_key,
    event_timestamp,
    current_timestamp() as current_time
from {{ ref('fct_events') }}
where event_timestamp > current_timestamp()