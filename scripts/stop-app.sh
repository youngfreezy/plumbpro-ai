#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[plumbpro]${NC} $*"; }

# Kill backend (uvicorn on port 8000)
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
  log "Killing backend (port 8000): PIDs $BACKEND_PIDS"
  echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || true
else
  log "No backend process found on port 8000."
fi

# Kill frontend (next dev on port 5100)
FRONTEND_PIDS=$(lsof -ti:5100 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
  log "Killing frontend (port 5100): PIDs $FRONTEND_PIDS"
  echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || true
else
  log "No frontend process found on port 5100."
fi

# Stop Docker services
if docker info >/dev/null 2>&1; then
  log "Stopping Docker services..."
  docker compose down 2>/dev/null || true
else
  log "Docker not running, skipping compose down."
fi

log "All services stopped."
