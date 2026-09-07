-- Per-player, per-season batting statistics: runs, balls faced,
-- dismissals, strike rate, and average.

with deliveries as (
    select
        f.*,
        m.season
    from {{ ref('fct_deliveries') }} f
    left join {{ ref('dim_matches') }} m on f.match_id = m.match_id
),

-- A "ball faced" excludes wides (extras that aren't off the bat), but for
-- simplicity here we count every delivery with a batter_id as a ball faced.
agg as (
    select
        batter_id,
        batter_name,
        season,
        sum(runs_batter) as total_runs,
        count(*) as balls_faced,
        sum(case when player_out = batter_name then 1 else 0 end) as dismissals
    from deliveries
    group by 1, 2, 3
)

select
    batter_id,
    batter_name,
    season,
    total_runs,
    balls_faced,
    dismissals,
    round(100.0 * total_runs / nullif(balls_faced, 0), 2) as strike_rate,
    round(
        total_runs::numeric / nullif(dismissals, 0), 2
    ) as batting_average
from agg
