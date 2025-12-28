#!/bin/bash
# Test script to debug frontend container issues

set -e

echo "=== Testing Frontend Container ==="

# Build the frontend image
echo "Building frontend image..."
docker compose -f docker-compose.yml build frontend

# Stop and remove existing container
echo "Stopping existing container..."
docker compose -f docker-compose.yml stop frontend 2>/dev/null || true
docker compose -f docker-compose.yml rm -f frontend 2>/dev/null || true

# Start frontend container
echo "Starting frontend container..."
docker compose -f docker-compose.yml up -d frontend

# Wait a moment
sleep 3

# Check container status
echo ""
echo "=== Container Status ==="
docker compose -f docker-compose.yml ps frontend

# Check logs
echo ""
echo "=== Container Logs (last 50 lines) ==="
docker compose -f docker-compose.yml logs --tail=50 frontend

# Try to exec into container and check nginx
echo ""
echo "=== Testing Nginx Configuration ==="
docker compose -f docker-compose.yml exec frontend nginx -t 2>&1 || echo "Nginx config test failed"

echo ""
echo "=== Checking Files ==="
docker compose -f docker-compose.yml exec frontend ls -la /usr/share/nginx/html/ 2>&1 || echo "Cannot list files"

echo ""
echo "=== Testing HTTP Response ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:1226/ || echo "Cannot connect to frontend"
