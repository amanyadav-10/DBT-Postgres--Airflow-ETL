-- Light cleanup layer over the raw matches table: renames, type casting,
-- and a stable surrogate key. No business logic lives here.

with source as (
    select * from {{ source('raw', 'matches') }}
)

select
    match_id,
    cast(match_date as date)   as match_date,
    season,
    team_1,
    team_2,
    venue,
    city,
    match_type,
    event_name
from source
