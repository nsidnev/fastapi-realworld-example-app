#!/usr/bin/env bash
set -ex

until nc -w 1 -z db 5432; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
sleep 2
>&2 echo "Postgres is up - executing command"

alembic upgrade head && uvicorn --host=0.0.0.0 app.main:app
