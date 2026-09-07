select
    match_id,
    match_date,
    season,
    team_1,
    team_2,
    venue,
    city,
    match_type,
    event_name
from {{ ref('stg_matches') }}
