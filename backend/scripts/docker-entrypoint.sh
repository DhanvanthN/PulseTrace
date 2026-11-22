#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for database..."
  python - <<'PY'
import os, sys, time
import psycopg
url = os.environ["DATABASE_URL"].replace("+psycopg", "")
for attempt in range(30):
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        sys.exit(0)
    except Exception:
        time.sleep(2)
print("Database not ready", file=sys.stderr)
sys.exit(1)
PY
fi

alembic upgrade head
exec "$@"