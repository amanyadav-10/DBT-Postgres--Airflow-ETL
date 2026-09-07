-- Every unique player who has appeared as a batter, bowler, non-striker,
-- or been dismissed, collapsed into a single player dimension.

with all_names as (
    select batter as player_name from {{ ref('stg_deliveries') }}
    union
    select bowler as player_name from {{ ref('stg_deliveries') }}
    union
    select non_striker as player_name from {{ ref('stg_deliveries') }}
    union
    select player_out as player_name from {{ ref('stg_deliveries') }} where player_out is not null
),

deduped as (
    select distinct player_name
    from all_names
    where player_name is not null
)

select
    {{ generate_surrogate_key(['player_name']) }} as player_id,
    player_name
from deduped
