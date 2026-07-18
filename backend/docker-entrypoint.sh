#!/bin/sh
set -eu

echo "Waiting for database..."
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)

for attempt in range(1, 61):
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except Exception as exc:
        if attempt == 60:
            print(f"Database is not ready: {exc}", file=sys.stderr)
            raise
        time.sleep(2)
PY

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
