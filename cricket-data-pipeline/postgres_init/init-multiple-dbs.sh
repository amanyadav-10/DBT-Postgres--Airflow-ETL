#!/bin/bash
# Runs automatically on first container startup (via docker-entrypoint-initdb.d).
# The base postgres image only creates one database by default (POSTGRES_DB);
# this script creates the second database ("cricket") that dbt/the pipeline uses,
# alongside Airflow's own metadata database.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE cricket;
EOSQL
