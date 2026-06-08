#!/usr/bin/env bash
# Environment validation script for AIPY-VN
# Validates required environment variables, service connectivity, and port availability
# Equivalent of scripts/check-env.ps1 for bash environments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# ─── Helper Functions ───────────────────────────────────────────────────────────

check_pass() {
    local name="$1"
    local detail="${2:-}"
    PASSED=$((PASSED + 1))
    if [ -n "$detail" ]; then
        echo -e "${GREEN}✅ $name: $detail${NC}"
    else
        echo -e "${GREEN}✅ $name${NC}"
    fi
}

check_fail() {
    local name="$1"
    local detail="${2:-}"
    FAILED=$((FAILED + 1))
    if [ -n "$detail" ]; then
        echo -e "${RED}❌ $name: $detail${NC}"
    else
        echo -e "${RED}❌ $name${NC}"
    fi
}

check_warn() {
    local name="$1"
    local detail="${2:-}"
    WARNINGS=$((WARNINGS + 1))
    if [ -n "$detail" ]; then
        echo -e "${YELLOW}⚠️  $name: $detail${NC}"
    else
        echo -e "${YELLOW}⚠️  $name${NC}"
    fi
}

check_port() {
    local port="$1"
    if command -v lsof &> /dev/null; then
        lsof -i ":$port" &> /dev/null
    elif command -v ss &> /dev/null; then
        ss -tlnp 2>/dev/null | grep -q ":${port} "
    elif command -v netstat &> /dev/null; then
        netstat -tlnp 2>/dev/null | grep -q ":${port} "
    else
        # Fallback: try to connect with bash
        (echo >/dev/tcp/localhost/$port) 2>/dev/null
    fi
}

check_env_var() {
    local env_file="$1"
    local var_name="$2"
    local required="${3:-true}"

    if [ ! -f "$env_file" ]; then
        if [ "$required" = "true" ]; then
            check_fail "$var_name" "File not found: $env_file"
        else
            check_warn "$var_name" "File not found: $env_file"
        fi
        return
    fi

    local value
    value=$(grep -E "^${var_name}=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2-)

    if [ -z "$value" ]; then
        if [ "$required" = "true" ]; then
            check_fail "$var_name" "Not set in $env_file"
        else
            check_warn "$var_name" "Not set (optional)"
        fi
    elif [ "$value" = "your-secret-key-here" ] || [ "$value" = "your-"* ]; then
        check_warn "$var_name" "Appears to be a placeholder value"
    else
        check_pass "$var_name" "Set"
    fi
}

# ─── Run Checks ─────────────────────────────────────────────────────────────────

echo -e "${CYAN}=== AIPY-VN Environment Check ===${NC}"
echo ""

# ─── 1. Tool Prerequisites ─────────────────────────────────────────────────────

echo -e "${CYAN}── Tool Prerequisites ──${NC}"

if command -v node &> /dev/null; then
    check_pass "Node.js" "$(node --version)"
else
    check_fail "Node.js" "Not installed"
fi

if command -v pnpm &> /dev/null; then
    check_pass "pnpm" "$(pnpm --version)"
else
    check_warn "pnpm" "Not installed (npm will be used as fallback)"
fi

if command -v python3 &> /dev/null; then
    check_pass "Python3" "$(python3 --version 2>&1)"
elif command -v python &> /dev/null; then
    check_pass "Python" "$(python --version 2>&1)"
else
    check_fail "Python" "Not installed"
fi

if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    check_pass "pip" "Installed"
else
    check_warn "pip" "Not found"
fi

if command -v uv &> /dev/null; then
    check_pass "uv" "$(uv --version)"
else
    check_warn "uv" "Not installed (recommended for Python dependency management)"
fi

if command -v docker &> /dev/null; then
    check_pass "Docker" "$(docker --version)"

    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        check_pass "Docker Daemon" "Running"
    else
        check_warn "Docker Daemon" "Not running (start Docker Desktop or dockerd)"
    fi
else
    check_warn "Docker" "Not installed (optional but recommended)"
fi

if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    check_pass "Docker Compose" "$(docker compose version --short 2>/dev/null || docker-compose --version 2>/dev/null)"
else
    check_warn "Docker Compose" "Not available"
fi

echo ""

# ─── 2. Environment Files ──────────────────────────────────────────────────────

echo -e "${CYAN}── Environment Files ──${NC}"

for env_file in \
    "$PROJECT_ROOT/.env" \
    "$PROJECT_ROOT/apps/api-server/.env" \
    "$PROJECT_ROOT/apps/web-admin/.env" \
    "$PROJECT_ROOT/apps/web-owner/.env" \
    "$PROJECT_ROOT/apps/web-customer/.env"
do
    local_name="${env_file#$PROJECT_ROOT/}"
    if [ -f "$env_file" ]; then
        check_pass "$local_name" "Exists"
    else
        check_fail "$local_name" "Missing (run ./scripts/setup-env.sh)"
    fi
done

echo ""

# ─── 3. Required Environment Variables ─────────────────────────────────────────

echo -e "${CYAN}── API Server Environment Variables ──${NC}"

API_ENV="$PROJECT_ROOT/apps/api-server/.env"

# Required variables
check_env_var "$API_ENV" "DATABASE_URL" "true"
check_env_var "$API_ENV" "REDIS_URL" "true"
check_env_var "$API_ENV" "QDRANT_URL" "true"
check_env_var "$API_ENV" "ENVIRONMENT" "true"
check_env_var "$API_ENV" "JWT_ALGORITHM" "true"
check_env_var "$API_ENV" "CORS_ORIGINS" "true"

# Optional but important
check_env_var "$API_ENV" "ECC_PRIVATE_KEY_PEM" "false"
check_env_var "$API_ENV" "CSRF_SECRET_KEY" "false"
check_env_var "$API_ENV" "SENTRY_DSN" "false"
check_env_var "$API_ENV" "OLLAMA_CLOUD_API_KEY" "false"
check_env_var "$API_ENV" "STRIPE_SECRET_KEY" "false"

echo ""

echo -e "${CYAN}── Frontend Environment Variables ──${NC}"

check_env_var "$PROJECT_ROOT/apps/web-admin/.env" "VITE_API_URL" "true"
check_env_var "$PROJECT_ROOT/apps/web-owner/.env" "VITE_API_URL" "true"
check_env_var "$PROJECT_ROOT/apps/web-customer/.env" "VITE_API_URL" "true"

echo ""

# ─── 4. Service Connectivity ───────────────────────────────────────────────────

echo -e "${CYAN}── Service Connectivity ──${NC}"

# Check PostgreSQL
PG_HOST="localhost"
PG_PORT="5432"
if check_port "$PG_PORT"; then
    check_pass "PostgreSQL" "Reachable on $PG_HOST:$PG_PORT"
else
    check_fail "PostgreSQL" "Not reachable on $PG_HOST:$PG_PORT"
fi

# Check Redis
REDIS_HOST="localhost"
REDIS_PORT="6379"
if check_port "$REDIS_PORT"; then
    check_pass "Redis" "Reachable on $REDIS_HOST:$REDIS_PORT"
else
    check_fail "Redis" "Not reachable on $REDIS_HOST:$REDIS_PORT"
fi

# Check Qdrant
QDRANT_HOST="localhost"
QDRANT_PORT="6333"
if check_port "$QDRANT_PORT"; then
    check_pass "Qdrant" "Reachable on $QDRANT_HOST:$QDRANT_PORT"
else
    check_warn "Qdrant" "Not reachable on $QDRANT_HOST:$QDRANT_PORT (may not be needed for all features)"
fi

# Check Docker containers if Docker is available
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo ""

    echo -e "${CYAN}── Docker Containers ──${NC}"

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "vietstore-postgres"; then
        check_pass "PostgreSQL Container" "Running"
    else
        check_warn "PostgreSQL Container" "Not running"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "vietstore-redis"; then
        check_pass "Redis Container" "Running"
    else
        check_warn "Redis Container" "Not running"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "vietstore-qdrant"; then
        check_pass "Qdrant Container" "Running"
    else
        check_warn "Qdrant Container" "Not running"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "vietstore-api"; then
        check_pass "API Server Container" "Running"
    else
        check_warn "API Server Container" "Not running"
    fi
fi

echo ""

# ─── 5. Port Availability ──────────────────────────────────────────────────────

echo -e "${CYAN}── Port Availability (for dev mode) ──${NC}"

for port_info in "9000:API Server" "3000:Customer App" "3001:Owner App" "3002:Admin App" "5432:PostgreSQL" "6379:Redis" "6333:Qdrant"; do
    port="${port_info%%:*}"
    name="${port_info#*:}"

    if check_port "$port"; then
        check_warn "$name (port $port)" "Port is in use"
    else
        check_pass "$name (port $port)" "Port available"
    fi
done

echo ""

# ─── 6. Project Structure ──────────────────────────────────────────────────────

echo -e "${CYAN}── Project Structure ──${NC}"

for dir in \
    "$PROJECT_ROOT/apps/api-server" \
    "$PROJECT_ROOT/apps/web-admin" \
    "$PROJECT_ROOT/apps/web-owner" \
    "$PROJECT_ROOT/apps/web-customer" \
    "$PROJECT_ROOT/scripts" \
    "$PROJECT_ROOT/docker-compose.yml"
do
    local_name="${dir#$PROJECT_ROOT/}"
    if [ -e "$dir" ]; then
        check_pass "$local_name" "Exists"
    else
        check_fail "$local_name" "Missing"
    fi
done

echo ""

# ─── Summary ────────────────────────────────────────────────────────────────────

TOTAL=$((PASSED + FAILED + WARNINGS))

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}✅ Passed:   $PASSED${NC}"
echo -e "  ${RED}❌ Failed:   $FAILED${NC}"
echo -e "  ${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "  📊 Total:    $TOTAL"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Environment check FAILED. Please fix the issues above before proceeding.${NC}"
    echo ""
    echo "Quick fixes:"
    echo "  - Missing .env files:  ./scripts/setup-env.sh"
    echo "  - Missing services:    docker compose up -d"
    echo "  - Full setup:          ./scripts/setup.sh"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Environment check passed with warnings. Review the warnings above.${NC}"
    exit 0
else
    echo -e "${GREEN}✅ All checks passed! Your environment is ready.${NC}"
    echo ""
    echo "Start services:  ./scripts/run.sh"
    exit 0
fi
