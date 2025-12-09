#!/bin/bash
# Test script for docker-compose configuration
# Validates: service definitions, health checks, dependencies, one-command startup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Docker Compose Configuration ===${NC}"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✓ Using Docker Compose v2${NC}"
else
    COMPOSE_CMD="docker-compose"
    echo -e "${YELLOW}⚠ Using Docker Compose v1${NC}"
fi

echo ""

# Function to validate compose file
validate_compose() {
    echo -e "${YELLOW}Validating docker-compose.yml...${NC}"

    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}Error: docker-compose.yml not found${NC}"
        return 1
    fi

    # Create temporary .env file if it doesn't exist (for validation only)
    if [ ! -f "env/.env" ]; then
        if [ -f "env/.env.example" ]; then
            cp env/.env.example env/.env
            TEMP_ENV=true
        else
            # Create minimal .env for validation
            mkdir -p env
            touch env/.env
            TEMP_ENV=true
        fi
    else
        TEMP_ENV=false
    fi

    # Validate compose file syntax
    if $COMPOSE_CMD config > /dev/null 2>&1; then
        echo -e "${GREEN}✓ docker-compose.yml syntax is valid${NC}"
    else
        echo -e "${RED}✗ docker-compose.yml syntax error${NC}"
        $COMPOSE_CMD config
        # Cleanup temp .env if created
        [ "$TEMP_ENV" = true ] && rm -f env/.env
        return 1
    fi

    # Cleanup temp .env if created
    [ "$TEMP_ENV" = true ] && rm -f env/.env

    # Check for required services
    local services=("db" "backend" "frontend")
    for service in "${services[@]}"; do
        if grep -q "^  ${service}:" docker-compose.yml; then
            echo -e "${GREEN}✓ Service '${service}' defined${NC}"
        else
            echo -e "${RED}✗ Service '${service}' not found${NC}"
            return 1
        fi
    done

    # Check for health checks
    if grep -q "healthcheck:" docker-compose.yml; then
        echo -e "${GREEN}✓ Health checks configured${NC}"
    else
        echo -e "${YELLOW}⚠ No health checks found${NC}"
    fi

    # Check for depends_on
    if grep -q "depends_on:" docker-compose.yml; then
        echo -e "${GREEN}✓ Service dependencies configured${NC}"
    else
        echo -e "${YELLOW}⚠ No service dependencies found${NC}"
    fi

    # Check for networks
    if grep -q "networks:" docker-compose.yml; then
        echo -e "${GREEN}✓ Networks configured${NC}"
    else
        echo -e "${YELLOW}⚠ No networks configured${NC}"
    fi

    # Check for volumes
    if grep -q "volumes:" docker-compose.yml; then
        echo -e "${GREEN}✓ Volumes configured${NC}"
    else
        echo -e "${YELLOW}⚠ No volumes configured${NC}"
    fi

    return 0
}

# Function to test compose config (dry run)
test_compose_config() {
    echo ""
    echo -e "${YELLOW}Testing compose configuration (dry run)...${NC}"

    # Show service list
    echo "Services:"
    $COMPOSE_CMD config --services | while read -r service; do
        echo "  - $service"
    done

    # Show port mappings
    echo ""
    echo "Port mappings:"
    $COMPOSE_CMD config | grep -A 2 "ports:" | grep -E "^\s+-" | sed 's/^/  /' || echo "  (none)"

    return 0
}

# Function to test one-command startup (if Docker daemon is running)
test_startup() {
    if ! docker info &> /dev/null; then
        echo ""
        echo -e "${YELLOW}⚠ Docker daemon is not running. Skipping startup test.${NC}"
        return 0
    fi

    echo ""
    echo -e "${YELLOW}Testing one-command startup...${NC}"
    echo "  (This will build images and start services)"
    echo ""

    # Build images
    echo -e "${BLUE}Building images...${NC}"
    if $COMPOSE_CMD build --quiet > /tmp/compose_build.log 2>&1; then
        echo -e "${GREEN}✓ Images built successfully${NC}"
    else
        echo -e "${RED}✗ Image build failed${NC}"
        echo "  See /tmp/compose_build.log for details"
        return 1
    fi

    # Start services
    echo -e "${BLUE}Starting services...${NC}"
    if $COMPOSE_CMD up -d > /tmp/compose_start.log 2>&1; then
        echo -e "${GREEN}✓ Services started${NC}"

        # Wait a bit for services to initialize
        sleep 5

        # Check service status
        echo ""
        echo -e "${BLUE}Service status:${NC}"
        $COMPOSE_CMD ps

        # Cleanup
        echo ""
        echo -e "${BLUE}Stopping services...${NC}"
        $COMPOSE_CMD down
        echo -e "${GREEN}✓ Services stopped${NC}"
    else
        echo -e "${RED}✗ Service startup failed${NC}"
        echo "  See /tmp/compose_start.log for details"
        $COMPOSE_CMD down 2>/dev/null || true
        return 1
    fi

    return 0
}

# Run validations
validate_compose
test_compose_config

# Optionally test startup (comment out if you don't want to build/start)
# test_startup

echo ""
echo -e "${GREEN}=== All compose validations passed ===${NC}"
