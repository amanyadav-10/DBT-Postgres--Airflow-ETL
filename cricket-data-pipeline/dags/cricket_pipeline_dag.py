"""
Airflow DAG for the Cricket Analytics Pipeline.

Pipeline stages:
  1. extract_matches   -> download_cricsheet.py (pull match JSON from Cricsheet)
  2. load_raw          -> load_raw.py (flatten JSON, load into Postgres raw schema)
  3. dbt_run           -> build staging + marts models
  4. dbt_test          -> run data quality tests; fails the DAG if a test fails

Runs daily by default. In practice, cricket match data doesn't change that
often, so this schedule is mainly here to demonstrate orchestration -
adjust `schedule_interval` to `None` for manual-trigger-only.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/opt/airflow/project"  # mounted path inside the Airflow container
DBT_PROJECT_DIR = f"{PROJECT_ROOT}/dbt_project"

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="cricket_pipeline",
    description="Extract Cricsheet data -> load to Postgres -> transform with dbt -> test",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["data-engineering", "dbt", "cricket"],
) as dag:

    extract_matches = BashOperator(
        task_id="extract_matches",
        bash_command=(
            f"python {PROJECT_ROOT}/ingestion/download_cricsheet.py "
            f"--competition ipl --limit 50 --out-dir {PROJECT_ROOT}/data/raw_json"
        ),
    )

    load_raw = BashOperator(
        task_id="load_raw",
        bash_command=(
            f"python {PROJECT_ROOT}/ingestion/load_raw.py "
            f"--json-dir {PROJECT_ROOT}/data/raw_json"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test",
    )

    extract_matches >> load_raw >> dbt_run >> dbt_test
