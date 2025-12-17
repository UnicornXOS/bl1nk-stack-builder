#!/usr/bin/env bash
# Start production environment

set -e

echo "Starting bl1nk-agent-builder production environment..."

# Start services
docker compose -f docker-compose.yml up --build -d

# Run database migrations
./scripts/run_migrations.sh

echo "Production environment started!"
echo ""
echo "Services are running in detached mode"
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
