#!/bin/bash
set -e

DB_HOST="${DATABASE_HOST:-db}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_USER="${DATABASE_USER:-liquidation_user}"
DB_PASS="${DATABASE_PASSWORD:-liquidation_pass}"
DB_NAME="${DATABASE_DB:-liquidation_db}"
POSTGRES_SUPERUSER="postgres"
POSTGRES_PASSWORD="postgres"  # superuser password from docker-compose

export PGPASSWORD="$POSTGRES_PASSWORD"

# Wait for the DB
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_SUPERUSER" >/dev/null 2>&1; do
    echo "Waiting for database..."
    sleep 1
done

# Create user if not exists
if ! psql -h "$DB_HOST" -U "$POSTGRES_SUPERUSER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "Creating user $DB_USER..."
    psql -h "$DB_HOST" -U "$POSTGRES_SUPERUSER" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
fi

# Create database if not exists
if ! psql -h "$DB_HOST" -U "$POSTGRES_SUPERUSER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    echo "Creating database $DB_NAME..."
    psql -h "$DB_HOST" -U "$POSTGRES_SUPERUSER" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
fi

# Alembic connects to the DB as $DB_USER
export PGPASSWORD="$DB_PASS"
alembic upgrade head

echo "Starting bot..."
exec python -m bot.main
