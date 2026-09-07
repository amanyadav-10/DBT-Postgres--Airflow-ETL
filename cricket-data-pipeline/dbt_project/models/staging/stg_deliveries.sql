-- One row per ball bowled. Adds a stable delivery_id surrogate key since
-- the raw data has no natural primary key at this grain.

with source as (
    select * from {{ source('raw', 'deliveries') }}
)

select
    {{ generate_surrogate_key(
        ['match_id', 'innings_num', 'over_num', 'ball_num']
    ) }} as delivery_id,
    match_id,
    innings_num,
    batting_team,
    over_num,
    ball_num,
    batter,
    bowler,
    non_striker,
    runs_batter,
    runs_extras,
    runs_total,
    player_out,
    wicket_kind,
    case when player_out is not null then 1 else 0 end as is_wicket
from source
