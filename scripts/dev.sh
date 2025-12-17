#!/usr/bin/env bash
# Start development environment

set -e

echo "Starting bl1nk-agent-builder development environment..."

# Activate virtual environment (Windows/Linux Path Check)
if [ -f ".venv/Scripts/activate" ]; then
    # shellcheck source=/dev/null
    source .venv/Scripts/activate  # Windows VENV Path
elif [ -f ".venv/bin/activate" ]; then
    # shellcheck source=/dev/null
    source .venv/bin/activate      # Linux/Mac VENV Path
fi

# Start services
docker compose -f docker-compose.yml up --build -d

# Run database migrations (must run after services are up)
./scripts/run_migrations.sh

echo "Development environment started!"
echo ""
echo "Services:"
echo "  - FastAPI Worker: http://localhost:8000"
echo "  - Cloudflare Worker: http://localhost:8787"
echo "  - UI: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin123)"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
