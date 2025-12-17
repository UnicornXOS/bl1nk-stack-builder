#!/usr/bin/env bash
# Check system health

set -e

echo "Checking bl1nk-agent-builder health..."

# Check Docker services
echo "Checking Docker services..."
docker compose ps

# Check API health
echo "Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI Worker: Healthy"
else
    echo "❌ FastAPI Worker: Unhealthy"
fi

# Check Worker bridge
echo "Checking Worker bridge..."
if curl -f http://localhost:8787/health > /dev/null 2>&1; then
    echo "✅ Cloudflare Worker: Healthy"
else
    echo "❌ Cloudflare Worker: Unhealthy"
fi

echo "Health check completed"
