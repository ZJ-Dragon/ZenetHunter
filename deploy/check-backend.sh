#!/bin/bash
# Backend Health Check Script
# This script checks if the backend is running and accessible

set -e

echo "=== Backend Health Check ==="
echo ""

# Check if backend container is running
if ! docker ps | grep -q zh-backend; then
    echo "❌ Backend container is not running"
    echo "   Run: docker compose up -d backend"
    exit 1
fi

echo "✓ Backend container is running"

# Check if backend is listening on port 8000
if ! nc -z localhost 8000 2>/dev/null; then
    echo "❌ Backend is not listening on port 8000"
    echo ""
    echo "Checking backend logs..."
    docker logs zh-backend --tail 50
    exit 1
fi

echo "✓ Backend is listening on port 8000"

# Check health endpoint
if curl -f -s http://localhost:8000/healthz > /dev/null; then
    echo "✓ Health check endpoint is responding"
else
    echo "❌ Health check endpoint is not responding"
    echo ""
    echo "Checking backend logs..."
    docker logs zh-backend --tail 50
    exit 1
fi

# Check database connection
echo ""
echo "Checking database connection..."
if docker exec zh-backend python -c "
import asyncio
import sys
from app.core.database import get_engine

async def check_db():
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        print('✓ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>&1; then
    echo "✓ Database connection is working"
else
    echo "❌ Database connection failed"
    echo ""
    echo "Make sure:"
    echo "  1. Database container is running: docker ps | grep zh-db"
    echo "  2. Database port is exposed: docker port zh-db"
    echo "  3. DATABASE_URL is set correctly (should use localhost:5432 with host network mode)"
    exit 1
fi

echo ""
echo "=== All checks passed ==="
echo "Backend is accessible at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
