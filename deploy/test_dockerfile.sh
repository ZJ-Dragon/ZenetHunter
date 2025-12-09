#!/bin/bash
# Test script for production Dockerfiles
# Validates: multi-stage builds, non-root users, minimal layers, image size

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Testing Production Dockerfiles ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}Warning: Docker daemon is not running. Skipping build tests.${NC}"
    echo "Dockerfile syntax validation only."
    echo ""
fi

# Function to validate Dockerfile syntax
validate_dockerfile() {
    local dockerfile=$1
    local name=$2
    
    echo -e "${YELLOW}Validating ${name}...${NC}"
    
    if [ ! -f "$dockerfile" ]; then
        echo -e "${RED}Error: ${dockerfile} not found${NC}"
        return 1
    fi
    
    # Check for multi-stage build
    if ! grep -q "FROM.*AS.*builder" "$dockerfile" && ! grep -q "FROM.*AS.*runtime" "$dockerfile"; then
        echo -e "${RED}Error: ${name} does not appear to use multi-stage build${NC}"
        return 1
    fi
    
    # Check for non-root user
    if ! grep -q "USER.*app\|USER.*[0-9]" "$dockerfile"; then
        echo -e "${RED}Error: ${name} does not set non-root user${NC}"
        return 1
    fi
    
    # Check for minimal layers (merged RUN commands)
    run_count=$(grep -c "^RUN" "$dockerfile" || true)
    if [ "$run_count" -gt 10 ]; then
        echo -e "${YELLOW}Warning: ${name} has ${run_count} RUN commands (consider merging)${NC}"
    fi
    
    echo -e "${GREEN}✓ ${name} syntax validation passed${NC}"
    return 0
}

# Function to test Docker build (if Docker is available)
test_build() {
    local dockerfile=$1
    local name=$2
    local tag=$3
    
    if ! docker info &> /dev/null; then
        return 0
    fi
    
    echo -e "${YELLOW}Building ${name}...${NC}"
    
    cd "$REPO_ROOT"
    if docker build -f "$dockerfile" -t "$tag" . > /tmp/docker_build_${name}.log 2>&1; then
        echo -e "${GREEN}✓ ${name} build successful${NC}"
        
        # Get image size
        local size=$(docker images "$tag" --format "{{.Size}}" | head -1)
        echo "  Image size: ${size}"
        
        # Count layers (approximate)
        local layers=$(docker history "$tag" --format "{{.ID}}" | wc -l | tr -d ' ')
        echo "  Layers: ${layers}"
        
        # Cleanup
        docker rmi "$tag" &> /dev/null || true
        
        return 0
    else
        echo -e "${RED}✗ ${name} build failed${NC}"
        echo "  See /tmp/docker_build_${name}.log for details"
        return 1
    fi
}

# Validate backend Dockerfile
echo "=== Backend Dockerfile ==="
validate_dockerfile "$SCRIPT_DIR/backend.Dockerfile" "backend.Dockerfile"
test_build "$SCRIPT_DIR/backend.Dockerfile" "backend" "zenethunter/backend:test"

echo ""

# Validate frontend Dockerfile
echo "=== Frontend Dockerfile ==="
validate_dockerfile "$SCRIPT_DIR/frontend.Dockerfile" "frontend.Dockerfile"
test_build "$SCRIPT_DIR/frontend.Dockerfile" "frontend" "zenethunter/frontend:test"

echo ""
echo -e "${GREEN}=== All Dockerfile validations passed ===${NC}"

