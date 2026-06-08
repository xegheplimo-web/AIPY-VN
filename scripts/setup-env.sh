#!/usr/bin/env bash
# Interactive environment setup script for AIPY-VN
# Prompts for key configuration values and writes to .env files

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

echo -e "${CYAN}=== AIPY-VN Environment Setup ===${NC}"
echo -e "${CYAN}This script will help you configure your .env files interactively.${NC}"
echo ""

# ─── Helper Functions ───────────────────────────────────────────────────────────

prompt_value() {
    local prompt="$1"
    local default="$2"
    local is_secret="${3:-false}"

    if [ "$is_secret" = "true" ]; then
        # For secrets, read silently
        if [ -n "$default" ]; then
            echo -ne "${CYAN}$prompt [${YELLOW}****${CYAN}]:${NC} "
        else
            echo -ne "${CYAN}$prompt:${NC} "
        fi
        read -rs value
        echo ""
    else
        if [ -n "$default" ]; then
            echo -ne "${CYAN}$prompt [${YELLOW}$default${CYAN}]:${NC} "
        else
            echo -ne "${CYAN}$prompt:${NC} "
        fi
        read -r value
    fi

    # Use default if empty
    if [ -z "$value" ] && [ -n "$default" ]; then
        value="$default"
    fi

    echo "$value"
}

write_env() {
    local env_file="$1"
    local key="$2"
    local value="$3"

    if [ -f "$env_file" ]; then
        # Check if key exists in file
        if rg -q "^${key}=" "$env_file" 2>/dev/null || grep -q "^${key}=" "$env_file" 2>/dev/null; then
            # Replace existing value
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^${key}=.*|${key}=${value}|" "$env_file"
            else
                sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
            fi
        else
            # Append new key
            echo "${key}=${value}" >> "$env_file"
        fi
    else
        echo "${key}=${value}" >> "$env_file"
    fi
}

confirm() {
    local prompt="$1"
    local default="${2:-n}"

    if [ "$default" = "y" ]; then
        echo -ne "${CYAN}$prompt [Y/n]:${NC} "
    else
        echo -ne "${CYAN}$prompt [y/N]:${NC} "
    fi
    read -r answer

    case "$answer" in
        [yY][eE][sS]|[yY]) return 0 ;;
        [nN][oO]|[nN]) return 1 ;;
        *) [ "$default" = "y" ] && return 0 || return 1 ;;
    esac
}

# ─── Check for Existing .env Files ─────────────────────────────────────────────

API_ENV="$PROJECT_ROOT/apps/api-server/.env"
ADMIN_ENV="$PROJECT_ROOT/apps/web-admin/.env"
OWNER_ENV="$PROJECT_ROOT/apps/web-owner/.env"
CUSTOMER_ENV="$PROJECT_ROOT/apps/web-customer/.env"
ROOT_ENV="$PROJECT_ROOT/.env"

echo -e "${CYAN}📁 Checking for existing .env files...${NC}"

for env_file in "$ROOT_ENV" "$API_ENV" "$ADMIN_ENV" "$OWNER_ENV" "$CUSTOMER_ENV"; do
    if [ -f "$env_file" ]; then
        echo -e "${YELLOW}⚠️  Found existing: $env_file${NC}"
    else
        echo -e "${GREEN}✅ Not found (will create): $env_file${NC}"
    fi
done

echo ""

if ! confirm "Continue with environment setup?" "y"; then
    echo "Aborted."
    exit 0
fi

# ─── API Server Configuration ──────────────────────────────────────────────────

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  API Server Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Ensure the .env file exists
if [ ! -f "$API_ENV" ]; then
    if [ -f "$PROJECT_ROOT/apps/api-server/.env.example" ]; then
        cp "$PROJECT_ROOT/apps/api-server/.env.example" "$API_ENV"
        echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    else
        touch "$API_ENV"
        echo -e "${GREEN}✅ Created empty .env file${NC}"
    fi
fi

echo ""
DATABASE_URL=$(prompt_value "Database URL (PostgreSQL)" "postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore")
write_env "$API_ENV" "DATABASE_URL" "$DATABASE_URL"

REDIS_URL=$(prompt_value "Redis URL" "redis://localhost:6379/0")
write_env "$API_ENV" "REDIS_URL" "$REDIS_URL"

QDRANT_URL=$(prompt_value "Qdrant URL" "http://localhost:6333")
write_env "$API_ENV" "QDRANT_URL" "$QDRANT_URL"

ENVIRONMENT=$(prompt_value "Environment (development/production)" "development")
write_env "$API_ENV" "ENVIRONMENT" "$ENVIRONMENT"

DEBUG=$(prompt_value "Debug mode (true/false)" "true")
write_env "$API_ENV" "DEBUG" "$DEBUG"

CORS_ORIGINS=$(prompt_value "CORS Origins (comma-separated)" "http://localhost:3000,http://localhost:5173,http://localhost:3001,http://localhost:3002")
write_env "$API_ENV" "CORS_ORIGINS" "$CORS_ORIGINS"

JWT_ALGORITHM=$(prompt_value "JWT Algorithm" "ES256")
write_env "$API_ENV" "JWT_ALGORITHM" "$JWT_ALGORITHM"

echo ""
echo -e "${YELLOW}⚠️  The following values are optional. Press Enter to skip.${NC}"
echo ""

ECC_PRIVATE_KEY=$(prompt_value "ECC Private Key PEM" "" "true")
if [ -n "$ECC_PRIVATE_KEY" ]; then
    write_env "$API_ENV" "ECC_PRIVATE_KEY_PEM" "$ECC_PRIVATE_KEY"
fi

CSRF_SECRET_KEY=$(prompt_value "CSRF Secret Key" "")
if [ -n "$CSRF_SECRET_KEY" ]; then
    write_env "$API_ENV" "CSRF_SECRET_KEY" "$CSRF_SECRET_KEY"
fi

OLLAMA_CLOUD_API_KEY=$(prompt_value "Ollama Cloud API Key" "" "true")
if [ -n "$OLLAMA_CLOUD_API_KEY" ]; then
    write_env "$API_ENV" "OLLAMA_CLOUD_API_KEY" "$OLLAMA_CLOUD_API_KEY"
fi

STRIPE_SECRET_KEY=$(prompt_value "Stripe Secret Key" "" "true")
if [ -n "$STRIPE_SECRET_KEY" ]; then
    write_env "$API_ENV" "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY"
fi

SENTRY_DSN=$(prompt_value "Sentry DSN" "")
if [ -n "$SENTRY_DSN" ]; then
    write_env "$API_ENV" "SENTRY_DSN" "$SENTRY_DSN"
fi

# ─── Frontend Configuration ────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Frontend Configuration${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

API_URL=$(prompt_value "API Server URL (for frontend apps)" "http://localhost:9000")

# Web Admin
if [ ! -f "$ADMIN_ENV" ]; then
    if [ -f "$PROJECT_ROOT/apps/web-admin/.env.example" ]; then
        cp "$PROJECT_ROOT/apps/web-admin/.env.example" "$ADMIN_ENV"
    else
        touch "$ADMIN_ENV"
    fi
fi
write_env "$ADMIN_ENV" "VITE_API_URL" "$API_URL"
echo -e "${GREEN}✅ Configured web-admin/.env${NC}"

# Web Owner
if [ ! -f "$OWNER_ENV" ]; then
    if [ -f "$PROJECT_ROOT/apps/web-owner/.env.example" ]; then
        cp "$PROJECT_ROOT/apps/web-owner/.env.example" "$OWNER_ENV"
    else
        touch "$OWNER_ENV"
    fi
fi
write_env "$OWNER_ENV" "VITE_API_URL" "$API_URL"
echo -e "${GREEN}✅ Configured web-owner/.env${NC}"

# Web Customer
if [ ! -f "$CUSTOMER_ENV" ]; then
    if [ -f "$PROJECT_ROOT/apps/web-customer/.env.example" ]; then
        cp "$PROJECT_ROOT/apps/web-customer/.env.example" "$CUSTOMER_ENV"
    else
        touch "$CUSTOMER_ENV"
    fi
fi
write_env "$CUSTOMER_ENV" "VITE_API_URL" "$API_URL"
echo -e "${GREEN}✅ Configured web-customer/.env${NC}"

# ─── Root .env ─────────────────────────────────────────────────────────────────

if [ ! -f "$ROOT_ENV" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ROOT_ENV"
        echo -e "${GREEN}✅ Created root .env from .env.example${NC}"
    fi
fi

# ─── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Environment Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Configured files:"
[ -f "$API_ENV" ] && echo -e "  ${GREEN}✅${NC} $API_ENV"
[ -f "$ADMIN_ENV" ] && echo -e "  ${GREEN}✅${NC} $ADMIN_ENV"
[ -f "$OWNER_ENV" ] && echo -e "  ${GREEN}✅${NC} $OWNER_ENV"
[ -f "$CUSTOMER_ENV" ] && echo -e "  ${GREEN}✅${NC} $CUSTOMER_ENV"
[ -f "$ROOT_ENV" ] && echo -e "  ${GREEN}✅${NC} $ROOT_ENV"
echo ""
echo -e "${YELLOW}IMPORTANT: Review the generated .env files and update any remaining values.${NC}"
echo -e "${YELLOW}In particular:${NC}"
echo "  - ECC_PRIVATE_KEY_PEM: Generate and set for JWT signing"
echo "  - CSRF_SECRET_KEY: Set a secure random string"
echo "  - SMTP credentials: Set if you need email notifications"
echo "  - Firebase credentials: Set if you need push notifications"
echo ""
echo "To validate your environment:  ./scripts/check-env.sh"
echo "To start services:              ./scripts/run.sh"
