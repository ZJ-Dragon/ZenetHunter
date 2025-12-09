#!/bin/bash
# ZenetHunter One-Command Startup Script
# This script sets up and starts all services with a single command

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ZenetHunter Startup ===${NC}"
echo ""

# Check if .env file exists
if [ ! -f "env/.env" ]; then
    echo -e "${YELLOW}⚠ env/.env not found. Creating from .env.example...${NC}"
    if [ -f "env/.env.example" ]; then
        cp env/.env.example env/.env
        echo -e "${GREEN}✓ Created env/.env from template${NC}"
        echo -e "${YELLOW}⚠ Please review and customize env/.env before production use${NC}"
    else
        echo -e "${YELLOW}⚠ env/.env.example not found. Using default values${NC}"
    fi
    echo ""
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${BLUE}Building images...${NC}"
$COMPOSE_CMD build

echo ""
echo -e "${BLUE}Starting services...${NC}"
$COMPOSE_CMD up -d

echo ""
echo -e "${GREEN}✓ All services started${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "  Frontend: http://localhost:1226"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/healthz"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  View logs: $COMPOSE_CMD logs -f"
echo "  Stop services: $COMPOSE_CMD down"
echo "  Restart services: $COMPOSE_CMD restart"
echo "  View status: $COMPOSE_CMD ps"
echo ""
