#!/bin/bash
set -e

wait_for_postgres() {
  echo "Waiting for PostgresSQL..."
  while ! pg_isready -h $DB_SERVER -p $DB_PORT -U $DB_USER -d $DB_NAME > /dev/null 2>&1; do
    echo "PostgresSQL is unavailable - sleeping 1 second"
    sleep 1
  done
  echo "PostgresSQL is up!"
}

wait_for_postgres

# applying migrations
echo "Applying database migrations..."
alembic upgrade head

# start the application
echo "Starting the application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload