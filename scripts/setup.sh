#!/usr/bin/env bash
# Setup script for AIPY-VN (VietStore RAG)
# Equivalent of scripts/setup.ps1 for bash environments

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

echo -e "${CYAN}=== AIPY-VN Setup ===${NC}"

# ─── Helper Functions ───────────────────────────────────────────────────────────

check_command() {
    local cmd="$1"
    local name="${2:-$cmd}"
    local min_version="${3:-}"

    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}❌ $name not found. Please install $name.${NC}"
        return 1
    fi

    local version
    version=$("$cmd" --version 2>&1 | head -1)
    echo -e "${GREEN}✅ $name: $version${NC}"
    return 0
}

copy_env_if_missing() {
    local env_file="$1"
    local env_example="$2"
    local label="${3:-}"

    if [ -f "$env_file" ]; then
        echo -e "${YELLOW}⚠️  $label .env already exists, skipping.${NC}"
    elif [ -f "$env_example" ]; then
        cp "$env_example" "$env_file"
        echo -e "${GREEN}✅ Created $label .env from .env.example${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env.example found for $label${NC}"
    fi
}

# ─── Check Prerequisites ────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}🔍 Checking prerequisites...${NC}"

errors=0

# Check Node.js
if ! check_command node "Node.js"; then
    echo -e "${RED}   Please install Node.js >= 18 from https://nodejs.org/${NC}"
    errors=$((errors + 1))
fi

# Check pnpm
if command -v pnpm &> /dev/null; then
    echo -e "${GREEN}✅ pnpm: $(pnpm --version)${NC}"
else
    echo -e "${YELLOW}⚠️  pnpm not found. Installing via npm...${NC}"
    npm install -g pnpm
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ pnpm installed: $(pnpm --version)${NC}"
    else
        echo -e "${RED}❌ Failed to install pnpm. Please install manually: npm install -g pnpm${NC}"
        errors=$((errors + 1))
    fi
fi

# Check Python
if ! check_command python3 "Python3"; then
    if ! check_command python "Python"; then
        echo -e "${RED}   Please install Python >= 3.11 from https://python.org/${NC}"
        errors=$((errors + 1))
    fi
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ pip3: $(pip3 --version 2>&1 | head -1)${NC}"
elif command -v pip &> /dev/null; then
    echo -e "${GREEN}✅ pip: $(pip --version 2>&1 | head -1)${NC}"
else
    echo -e "${YELLOW}⚠️  pip not found. Python package installation may fail.${NC}"
fi

# Check uv (Python package manager)
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✅ uv: $(uv --version)${NC}"
else
    echo -e "${YELLOW}⚠️  uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not found. You can still develop without Docker.${NC}"
fi

if [ $errors -gt 0 ]; then
    echo -e "${RED}❌ $errors prerequisite(s) missing. Please install them and re-run.${NC}"
    exit 1
fi

# ─── Install Dependencies ───────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}📦 Installing root dependencies...${NC}"
cd "$PROJECT_ROOT"

if command -v pnpm &> /dev/null; then
    pnpm install
else
    npm install
fi

# ─── Create .env Files ──────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}🔧 Setting up environment files...${NC}"

copy_env_if_missing \
    "$PROJECT_ROOT/.env" \
    "$PROJECT_ROOT/.env.example" \
    "Root"

copy_env_if_missing \
    "$PROJECT_ROOT/apps/api-server/.env" \
    "$PROJECT_ROOT/apps/api-server/.env.example" \
    "API Server"

copy_env_if_missing \
    "$PROJECT_ROOT/apps/web-admin/.env" \
    "$PROJECT_ROOT/apps/web-admin/.env.example" \
    "Web Admin"

copy_env_if_missing \
    "$PROJECT_ROOT/apps/web-owner/.env" \
    "$PROJECT_ROOT/apps/web-owner/.env.example" \
    "Web Owner"

copy_env_if_missing \
    "$PROJECT_ROOT/apps/web-customer/.env" \
    "$PROJECT_ROOT/apps/web-customer/.env.example" \
    "Web Customer"

# ─── Start Docker Services ──────────────────────────────────────────────────────

if command -v docker &> /dev/null; then
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo ""
        echo -e "${CYAN}🐳 Starting Docker services...${NC}"
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d

        echo ""
        echo -e "${CYAN}⏳ Waiting for PostgreSQL to be ready...${NC}"
        sleep 5

        # Wait for postgres to actually be ready
        max_attempts=30
        attempt=0
        until docker exec vietstore-postgres pg_isready -U postgres &> /dev/null || [ $attempt -ge $max_attempts ]; do
            attempt=$((attempt + 1))
            echo -e "${YELLOW}   Waiting... (attempt $attempt/$max_attempts)${NC}"
            sleep 2
        done

        if [ $attempt -ge $max_attempts ]; then
            echo -e "${YELLOW}⚠️  PostgreSQL did not become ready in time. Check your Docker setup.${NC}"
        else
            echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  docker-compose.yml not found, skipping Docker services.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not available, skipping Docker services.${NC}"
    echo -e "${YELLOW}   Make sure PostgreSQL and Redis are running manually.${NC}"
fi

# ─── Run Database Migrations ────────────────────────────────────────────────────

if [ -d "$PROJECT_ROOT/apps/api-server" ]; then
    echo ""
    echo -e "${CYAN}🗄️  Running database migrations...${NC}"
    cd "$PROJECT_ROOT/apps/api-server"

    if command -v uv &> /dev/null; then
        PYTHONPATH="$PROJECT_ROOT" uv run alembic upgrade head 2>&1 || {
            echo -e "${YELLOW}⚠️  Database migration failed. Make sure PostgreSQL is running and .env is configured.${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  uv not found, skipping migrations. Install uv to run migrations.${NC}"
    fi

    # Seed data
    echo ""
    echo -e "${CYAN}🌱 Seeding database with sample data...${NC}"
    if command -v uv &> /dev/null; then
        PYTHONPATH="$PROJECT_ROOT/apps/api-server" uv run python src/seed.py 2>&1 || {
            echo -e "${YELLOW}⚠️  Database seeding failed. You can run it manually later.${NC}"
        }
    fi
fi

cd "$PROJECT_ROOT"

# ─── Build Frontend Packages ────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}🏗️  Building frontend packages...${NC}"

for app in web-admin web-owner web-customer; do
    if [ -d "$PROJECT_ROOT/apps/$app" ]; then
        echo -e "${CYAN}   Building $app...${NC}"
        cd "$PROJECT_ROOT/apps/$app"
        if command -v pnpm &> /dev/null; then
            pnpm build 2>&1 || {
                echo -e "${YELLOW}⚠️  Build failed for $app. You can build it manually later.${NC}"
            }
        else
            npm run build 2>&1 || {
                echo -e "${YELLOW}⚠️  Build failed for $app. You can build it manually later.${NC}"
            }
        fi
    fi
done

cd "$PROJECT_ROOT"

# ─── Done ───────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}[OK] Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review and update .env files if needed (run ./scripts/setup-env.sh for interactive setup)"
echo "  2. Start services:  ./scripts/run.sh"
echo "     Or individually:"
echo "     - Backend:   cd apps/api-server && uv run uvicorn src.main:app --reload --port 9000"
echo "     - Frontend:  cd apps/web-customer && pnpm dev"
echo "  3. Check environment:  ./scripts/check-env.sh"
