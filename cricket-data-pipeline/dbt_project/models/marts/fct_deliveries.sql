-- The core fact table: one row per ball bowled, with foreign keys to
-- dim_players (batter/bowler) and dim_matches.

with deliveries as (
    select * from {{ ref('stg_deliveries') }}
),

batters as (
    select player_id as batter_id, player_name from {{ ref('dim_players') }}
),

bowlers as (
    select player_id as bowler_id, player_name from {{ ref('dim_players') }}
)

select
    d.delivery_id,
    d.match_id,
    d.innings_num,
    d.batting_team,
    d.over_num,
    d.ball_num,
    b1.batter_id,
    d.batter as batter_name,
    b2.bowler_id,
    d.bowler as bowler_name,
    d.non_striker,
    d.runs_batter,
    d.runs_extras,
    d.runs_total,
    d.is_wicket,
    d.wicket_kind,
    d.player_out
from deliveries d
left join batters b1 on d.batter = b1.player_name
left join bowlers b2 on d.bowler = b2.player_name
