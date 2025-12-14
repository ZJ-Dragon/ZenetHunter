#!/bin/bash
# Security baseline verification script
# Validates: health checks, resource limits, least privilege, file system security

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}=== ZenetHunter Security Baseline Verification ===${NC}"
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
else
    COMPOSE_CMD="docker-compose"
fi

# Function to check and report
check_pass() {
    local test_name=$1
    echo -e "${GREEN}✓${NC} ${test_name}"
    ((PASSED++))
}

check_fail() {
    local test_name=$1
    local message=$2
    echo -e "${RED}✗${NC} ${test_name}"
    if [ -n "$message" ]; then
        echo "  ${message}"
    fi
    ((FAILED++))
}

check_warn() {
    local test_name=$1
    local message=$2
    echo -e "${YELLOW}⚠${NC} ${test_name}"
    if [ -n "$message" ]; then
        echo "  ${message}"
    fi
    ((WARNINGS++))
}

# Check if services are running
if ! docker ps | grep -q "zh-backend\|zh-frontend\|zh-db"; then
    echo -e "${YELLOW}⚠ Services are not running. Starting services for testing...${NC}"
    $COMPOSE_CMD up -d > /dev/null 2>&1
    sleep 5
fi

echo -e "${BLUE}=== 1. Health Checks ===${NC}"

# Check health check configuration
if grep -q "healthcheck:" docker-compose.yml; then
    check_pass "Health checks configured in docker-compose.yml"
else
    check_fail "Health checks not found in docker-compose.yml"
fi

# Check health check status
if docker ps --format "{{.Names}}\t{{.Status}}" | grep -q "healthy"; then
    check_pass "Services report healthy status"
else
    check_warn "Some services may not be healthy (check: docker compose ps)"
fi

echo ""

echo -e "${BLUE}=== 2. Resource Limits ===${NC}"

# Check resource limits in compose file
if grep -q "deploy:" docker-compose.yml && grep -q "resources:" docker-compose.yml; then
    check_pass "Resource limits configured in docker-compose.yml"
else
    check_fail "Resource limits not found in docker-compose.yml"
fi

# Check CPU limits
if grep -q "cpus:" docker-compose.yml; then
    check_pass "CPU limits configured"
else
    check_fail "CPU limits not configured"
fi

# Check memory limits
if grep -q "memory:" docker-compose.yml; then
    check_pass "Memory limits configured"
else
    check_fail "Memory limits not configured"
fi

echo ""

echo -e "${BLUE}=== 3. Least Privilege ===${NC}"

# Check non-root user configuration
if grep -q 'user: "101:101"' docker-compose.yml || grep -q 'user: "70:70"' docker-compose.yml; then
    check_pass "Non-root users configured"
else
    check_fail "Non-root users not configured"
fi

# Check capability management
if grep -q "cap_drop:" docker-compose.yml && grep -q "cap_add:" docker-compose.yml; then
    check_pass "Capability management configured"
else
    check_fail "Capability management not configured"
fi

# Check privilege escalation prevention
if grep -q "no-new-privileges" docker-compose.yml; then
    check_pass "Privilege escalation disabled"
else
    check_fail "Privilege escalation prevention not configured"
fi

# Verify actual non-root execution (if containers are running)
if docker ps | grep -q "zh-backend"; then
    USER_ID=$(docker inspect zh-backend --format '{{.Config.User}}' 2>/dev/null || echo "")
    if [ -n "$USER_ID" ] && [ "$USER_ID" != "0" ] && [ "$USER_ID" != "0:0" ]; then
        check_pass "Backend runs as non-root (${USER_ID})"
    else
        check_fail "Backend may be running as root"
    fi
fi

echo ""

echo -e "${BLUE}=== 4. File System Security ===${NC}"

# Check read-only filesystem
if grep -q "read_only: true" docker-compose.yml; then
    check_pass "Read-only filesystem configured"
else
    check_warn "Read-only filesystem not configured (may be intentional for database)"
fi

# Check tmpfs configuration
if grep -q "tmpfs:" docker-compose.yml; then
    check_pass "Tmpfs configured for writable areas"
else
    check_warn "Tmpfs not configured"
fi

echo ""

echo -e "${BLUE}=== 5. Network Security ===${NC}"

# Check network isolation
if grep -q "networks:" docker-compose.yml; then
    check_pass "Network configuration present"
else
    check_fail "Network configuration missing"
fi

# Check database port exposure (should not be exposed)
if grep -A 5 "db:" docker-compose.yml | grep -q "ports:"; then
    check_warn "Database port may be exposed (should be internal only)"
else
    check_pass "Database not exposed to host"
fi

echo ""

echo -e "${BLUE}=== 6. Environment Security ===${NC}"

# Check for secret management
if grep -q "SECRET_KEY" docker-compose.yml && ! grep -q "SECRET_KEY.*insecure" docker-compose.yml; then
    check_pass "Secret key configuration present"
else
    check_warn "Secret key may use default value (check .env file)"
fi

# Check Python security environment variables
if grep -q "PYTHONDONTWRITEBYTECODE" docker-compose.yml; then
    check_pass "Python security environment variables configured"
else
    check_warn "Python security environment variables not explicitly set"
fi

echo ""

echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Security baseline verification passed${NC}"
    exit 0
else
    echo -e "${RED}✗ Security baseline verification failed${NC}"
    exit 1
fi
