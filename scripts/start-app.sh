#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

SKIP_DOCKER=false
for arg in "$@"; do
  case "$arg" in
    --no-docker) SKIP_DOCKER=true ;;
  esac
done

# ---------- colours ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[plumbpro]${NC} $*"; }
warn() { echo -e "${YELLOW}[plumbpro]${NC} $*"; }
err()  { echo -e "${RED}[plumbpro]${NC} $*"; }

# ---------- cleanup on exit ----------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  log "Shutting down..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  if [ "$SKIP_DOCKER" = false ]; then
    docker compose down 2>/dev/null || true
  fi
  log "Done."
  exit 0
}
trap cleanup SIGINT SIGTERM

# ---------- Docker ----------
if [ "$SKIP_DOCKER" = false ]; then
  if ! docker info >/dev/null 2>&1; then
    warn "Docker is not running. Attempting to start Docker Desktop..."
    open -a Docker
    # Wait up to 60 seconds for Docker to be ready
    TRIES=0
    MAX_TRIES=60
    while ! docker info >/dev/null 2>&1; do
      TRIES=$((TRIES + 1))
      if [ "$TRIES" -ge "$MAX_TRIES" ]; then
        err "Docker failed to start after ${MAX_TRIES}s. Exiting."
        exit 1
      fi
      sleep 1
    done
    log "Docker is ready."
  fi

  log "Starting Docker services..."
  docker compose up -d

  # Wait for Postgres
  log "Waiting for Postgres..."
  TRIES=0
  MAX_TRIES=30
  while ! docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-plumbpro}" -d "${POSTGRES_DB:-plumbpro}" >/dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge "$MAX_TRIES" ]; then
      err "Postgres failed to become ready after ${MAX_TRIES}s."
      exit 1
    fi
    sleep 1
  done
  log "Postgres is healthy."

  # Wait for Redis
  log "Waiting for Redis..."
  TRIES=0
  MAX_TRIES=30
  REDIS_PW="${REDIS_PASSWORD:-$(grep REDIS_PASSWORD .env 2>/dev/null | cut -d= -f2)}"
  while ! docker compose exec -T redis redis-cli -a "$REDIS_PW" ping 2>/dev/null | grep -q PONG; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge "$MAX_TRIES" ]; then
      err "Redis failed to become ready after ${MAX_TRIES}s."
      exit 1
    fi
    sleep 1
  done
  log "Redis is healthy."
else
  warn "Skipping Docker (--no-docker). Make sure Postgres and Redis are running."
fi

# ---------- Backend ----------
log "Starting backend on :8000..."
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
  warn "No venv found. Creating one..."
  python3.11 -m venv "$PROJECT_ROOT/backend/venv"
  source "$PROJECT_ROOT/backend/venv/bin/activate"
  pip install -r "$PROJECT_ROOT/backend/requirements.txt"
else
  source "$PROJECT_ROOT/backend/venv/bin/activate"
fi
cd "$PROJECT_ROOT"
uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ---------- Frontend ----------
log "Starting frontend on :5100..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
  warn "No node_modules found. Running npm install..."
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

log "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
log "Backend:  http://localhost:8000"
log "Frontend: http://localhost:5100"
log "MinIO:    http://localhost:9001 (console)"
log ""
log "Press Ctrl+C to stop all services."

# Wait for both processes
wait "$BACKEND_PID" "$FRONTEND_PID"
