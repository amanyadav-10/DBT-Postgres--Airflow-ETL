"""
Load step: parses Cricsheet match JSON files (as saved by download_cricsheet.py)
into two flat tables and loads them into Postgres:

  raw.matches     - one row per match (teams, venue, date, season, etc.)
  raw.deliveries  - one row per ball bowled (batter, bowler, runs, wicket info)

Cricsheet's JSON format (schema v2+) roughly looks like:
{
  "info": {
      "dates": ["2023-04-01"],
      "teams": ["Team A", "Team B"],
      "venue": "Some Stadium",
      "city": "Some City",
      "season": "2023",
      "match_type": "T20",
      "event": {"name": "Indian Premier League"}
  },
  "innings": [
    {
      "team": "Team A",
      "overs": [
        {
          "over": 0,
          "deliveries": [
            {
              "batter": "Player 1",
              "bowler": "Player 2",
              "non_striker": "Player 3",
              "runs": {"batter": 1, "extras": 0, "total": 1},
              "wickets": [{"player_out": "Player 1", "kind": "caught"}]  # optional
            },
            ...
          ]
        },
        ...
      ]
    },
    ...
  ]
}

Usage:
    python load_raw.py --json-dir data/raw_json --db-url postgresql://airflow:airflow@localhost:5432/cricket
"""

import argparse
import json
import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DEFAULT_DB_URL = os.environ.get(
    "CRICKET_DB_URL", "postgresql://airflow:airflow@localhost:5432/cricket"
)


def parse_match(match_id: str, match_json: dict) -> tuple[dict, list[dict]]:
    """Parses one Cricsheet match JSON into a match row + list of delivery rows."""
    info = match_json.get("info", {})
    dates = info.get("dates", [])
    teams = info.get("teams", [])
    event = info.get("event", {}) or {}

    match_row = {
        "match_id": match_id,
        "match_date": dates[0] if dates else None,
        "season": info.get("season"),
        "team_1": teams[0] if len(teams) > 0 else None,
        "team_2": teams[1] if len(teams) > 1 else None,
        "venue": info.get("venue"),
        "city": info.get("city"),
        "match_type": info.get("match_type"),
        "event_name": event.get("name"),
    }

    delivery_rows = []
    for innings_num, innings in enumerate(match_json.get("innings", []), start=1):
        batting_team = innings.get("team")
        for over in innings.get("overs", []):
            over_num = over.get("over")
            for ball_num, delivery in enumerate(over.get("deliveries", []), start=1):
                runs = delivery.get("runs", {})
                wickets = delivery.get("wickets", [])
                player_out = wickets[0]["player_out"] if wickets else None
                wicket_kind = wickets[0]["kind"] if wickets else None

                delivery_rows.append(
                    {
                        "match_id": match_id,
                        "innings_num": innings_num,
                        "batting_team": batting_team,
                        "over_num": over_num,
                        "ball_num": ball_num,
                        "batter": delivery.get("batter"),
                        "bowler": delivery.get("bowler"),
                        "non_striker": delivery.get("non_striker"),
                        "runs_batter": runs.get("batter", 0),
                        "runs_extras": runs.get("extras", 0),
                        "runs_total": runs.get("total", 0),
                        "player_out": player_out,
                        "wicket_kind": wicket_kind,
                    }
                )

    return match_row, delivery_rows


def load_all(json_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    match_rows, delivery_rows = [], []
    files = sorted(json_dir.glob("*.json"))
    print(f"Found {len(files)} match files in {json_dir}")

    for path in files:
        match_id = path.stem
        with open(path) as f:
            match_json = json.load(f)
        match_row, deliveries = parse_match(match_id, match_json)
        match_rows.append(match_row)
        delivery_rows.extend(deliveries)

    return pd.DataFrame(match_rows), pd.DataFrame(delivery_rows)


def write_to_postgres(matches_df: pd.DataFrame, deliveries_df: pd.DataFrame, db_url: str):
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.matches (
            match_id TEXT PRIMARY KEY,
            match_date DATE,
            season TEXT,
            team_1 TEXT,
            team_2 TEXT,
            venue TEXT,
            city TEXT,
            match_type TEXT,
            event_name TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.deliveries (
            match_id TEXT,
            innings_num INT,
            batting_team TEXT,
            over_num INT,
            ball_num INT,
            batter TEXT,
            bowler TEXT,
            non_striker TEXT,
            runs_batter INT,
            runs_extras INT,
            runs_total INT,
            player_out TEXT,
            wicket_kind TEXT
        );
        """
    )
    # Idempotent reload: clear before inserting so re-runs don't duplicate rows.
    cur.execute("TRUNCATE raw.matches, raw.deliveries;")

    if not matches_df.empty:
        execute_values(
            cur,
            "INSERT INTO raw.matches VALUES %s",
            list(matches_df.itertuples(index=False, name=None)),
        )
    if not deliveries_df.empty:
        execute_values(
            cur,
            "INSERT INTO raw.deliveries VALUES %s",
            list(deliveries_df.itertuples(index=False, name=None)),
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(matches_df)} matches and {len(deliveries_df)} deliveries into Postgres.")


def main():
    parser = argparse.ArgumentParser(description="Load Cricsheet JSON into Postgres raw schema.")
    parser.add_argument("--json-dir", default="data/raw_json")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL)
    args = parser.parse_args()

    matches_df, deliveries_df = load_all(Path(args.json_dir))
    write_to_postgres(matches_df, deliveries_df, args.db_url)


if __name__ == "__main__":
    main()
