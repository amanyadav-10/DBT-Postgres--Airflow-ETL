-- Per-player, per-season bowling statistics: wickets, runs conceded,
-- overs bowled, and economy rate.

with deliveries as (
    select
        f.*,
        m.season
    from {{ ref('fct_deliveries') }} f
    left join {{ ref('dim_matches') }} m on f.match_id = m.match_id
),

agg as (
    select
        bowler_id,
        bowler_name,
        season,
        count(*) as balls_bowled,
        sum(runs_total) as runs_conceded,
        sum(is_wicket) as wickets
    from deliveries
    group by 1, 2, 3
)

select
    bowler_id,
    bowler_name,
    season,
    balls_bowled,
    round(balls_bowled / 6.0, 1) as overs_bowled,
    runs_conceded,
    wickets,
    round(6.0 * runs_conceded / nullif(balls_bowled, 0), 2) as economy_rate
from agg
