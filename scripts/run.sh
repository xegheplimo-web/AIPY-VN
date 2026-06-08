#!/usr/bin/env bash
# Run script for AIPY-VN
# Starts services via docker-compose or individually in dev mode
# Equivalent of scripts/run.ps1 for bash environments

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

# ─── Usage ──────────────────────────────────────────────────────────────────────

usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  docker     Start all services via docker-compose (default)"
    echo "  backend    Start the backend API server in dev mode"
    echo "  frontend   Start the customer frontend in dev mode"
    echo "  admin      Start the admin frontend in dev mode"
    echo "  owner      Start the owner frontend in dev mode"
    echo "  all        Start all services in dev mode (backend + all frontends)"
    echo "  stop       Stop docker-compose services"
    echo "  logs       Tail docker-compose logs"
    echo ""
    echo "Options:"
    echo "  -d, --detach    Run docker services in detached mode (default)"
    echo "  -a, --attach    Run docker services in attached mode (with logs)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker              # Start all services with docker-compose"
    echo "  $0 backend             # Start API server on port 9000"
    echo "  $0 frontend            # Start customer app on port 3000"
    echo "  $0 admin               # Start admin app on port 3002"
    echo "  $0 owner               # Start owner app on port 3001"
    echo "  $0 all                 # Start everything in dev mode"
    echo "  $0 stop                # Stop docker services"
}

# ─── Parse Arguments ───────────────────────────────────────────────────────────

COMMAND="docker"
DETACH=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        docker|backend|frontend|admin|owner|all|stop|logs)
            COMMAND="$1"
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -a|--attach)
            DETACH=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# ─── Functions ──────────────────────────────────────────────────────────────────

start_docker() {
    echo -e "${CYAN}🐳 Starting all services with docker-compose...${NC}"

    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo -e "${RED}❌ docker-compose.yml not found at $PROJECT_ROOT/docker-compose.yml${NC}"
        exit 1
    fi

    if [ "$DETACH" = true ]; then
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
    else
        docker compose -f "$PROJECT_ROOT/docker-compose.yml" up
    fi

    echo ""
    echo -e "${GREEN}✅ Services started!${NC}"
    echo "  Backend:   http://localhost:9000"
    echo "  API Docs:  http://localhost:9000/docs"
    echo "  Customer:  http://localhost:3000"
    echo "  Owner:     http://localhost:3001"
    echo "  Admin:     http://localhost:3002"
    echo "  Grafana:   http://localhost:3003"
}

start_backend() {
    echo -e "${CYAN}🚀 Starting backend API server...${NC}"

    local api_dir="$PROJECT_ROOT/apps/api-server"
    if [ ! -d "$api_dir" ]; then
        echo -e "${RED}❌ API server directory not found: $api_dir${NC}"
        exit 1
    fi

    cd "$api_dir"
    export PYTHONPATH="$PROJECT_ROOT"

    if command -v uv &> /dev/null; then
        echo -e "${GREEN}Starting with uv...${NC}"
        uv run uvicorn src.main:app --reload --port 9000
    else
        echo -e "${YELLOW}⚠️  uv not found, using python directly...${NC}"
        python3 -m uvicorn src.main:app --reload --port 9000
    fi
}

start_frontend() {
    local app_name="$1"
    local port="${2:-3000}"
    local app_dir="$PROJECT_ROOT/apps/$app_name"

    echo -e "${CYAN}🚀 Starting $app_name frontend on port $port...${NC}"

    if [ ! -d "$app_dir" ]; then
        echo -e "${RED}❌ Directory not found: $app_dir${NC}"
        exit 1
    fi

    cd "$app_dir"

    if command -v pnpm &> /dev/null; then
        pnpm dev --port "$port"
    else
        npm run dev -- --port "$port"
    fi
}

start_all_dev() {
    echo -e "${CYAN}🚀 Starting all services in dev mode...${NC}"
    echo ""

    # Array to store background PIDs
    local pids=()

    # Start backend
    (
        cd "$PROJECT_ROOT/apps/api-server"
        export PYTHONPATH="$PROJECT_ROOT"
        if command -v uv &> /dev/null; then
            uv run uvicorn src.main:app --reload --port 9000
        else
            python3 -m uvicorn src.main:app --reload --port 9000
        fi
    ) &
    pids+=($!)
    echo -e "${GREEN}✅ Backend started (PID: $!, port: 9000)${NC}"

    # Start customer frontend
    (
        cd "$PROJECT_ROOT/apps/web-customer"
        if command -v pnpm &> /dev/null; then
            pnpm dev --port 3000
        else
            npm run dev -- --port 3000
        fi
    ) &
    pids+=($!)
    echo -e "${GREEN}✅ Customer app started (PID: $!, port: 3000)${NC}"

    # Start owner frontend
    (
        cd "$PROJECT_ROOT/apps/web-owner"
        if command -v pnpm &> /dev/null; then
            pnpm dev --port 3001
        else
            npm run dev -- --port 3001
        fi
    ) &
    pids+=($!)
    echo -e "${GREEN}✅ Owner app started (PID: $!, port: 3001)${NC}"

    # Start admin frontend
    (
        cd "$PROJECT_ROOT/apps/web-admin"
        if command -v pnpm &> /dev/null; then
            pnpm dev --port 3002
        else
            npm run dev -- --port 3002
        fi
    ) &
    pids+=($!)
    echo -e "${GREEN}✅ Admin app started (PID: $!, port: 3002)${NC}"

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  All services running!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  Backend:   http://localhost:9000"
    echo "  API Docs:  http://localhost:9000/docs"
    echo "  Customer:  http://localhost:3000"
    echo "  Owner:     http://localhost:3001"
    echo "  Admin:     http://localhost:3002"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""

    # Trap Ctrl+C to kill all background processes
    trap 'echo -e "\n${YELLOW}Stopping all services...${NC}"; kill ${pids[@]} 2>/dev/null; exit 0' INT TERM

    # Wait for any process to exit
    wait
}

stop_docker() {
    echo -e "${CYAN}🛑 Stopping docker-compose services...${NC}"
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" down
    echo -e "${GREEN}✅ All docker services stopped.${NC}"
}

show_logs() {
    echo -e "${CYAN}📋 Tailing docker-compose logs...${NC}"
    docker compose -f "$PROJECT_ROOT/docker-compose.yml" logs -f
}

# ─── Execute Command ───────────────────────────────────────────────────────────

case "$COMMAND" in
    docker)
        start_docker
        ;;
    backend)
        start_backend
        ;;
    frontend)
        start_frontend "web-customer" 3000
        ;;
    admin)
        start_frontend "web-admin" 3002
        ;;
    owner)
        start_frontend "web-owner" 3001
        ;;
    all)
        start_all_dev
        ;;
    stop)
        stop_docker
        ;;
    logs)
        show_logs
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        usage
        exit 1
        ;;
esac
