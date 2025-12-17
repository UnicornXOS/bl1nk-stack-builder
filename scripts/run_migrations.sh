#!/usr/bin/env bash
# Run database migrations using the Docker container

set -e

CONTAINER_NAME="bl1nk-postgres"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Waiting for postgres container to be healthy..."

MAX_WAIT_SECONDS=60
START_TIME=$(date +%s)

while true; do
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        break
    fi

    NOW=$(date +%s)
    ELAPSED=$((NOW - START_TIME))
    if [ "$ELAPSED" -ge "$MAX_WAIT_SECONDS" ]; then
        echo "❌ Postgres container did not become healthy within ${MAX_WAIT_SECONDS}s. Last status: $STATUS"
        exit 1
    fi

    sleep 1
done

echo "Running database migrations..."

# Run the init-db.sql script manually on the running container
if ! docker exec -i "$CONTAINER_NAME" psql -U bl1nk_user -d bl1nk < "$PROJECT_ROOT/init-db.sql"; then
    echo "❌ Failed to run init-db.sql"
    exit 1
fi

echo "Database migrations completed successfully (using init-db.sql as migration)"
