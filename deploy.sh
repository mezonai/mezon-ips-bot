#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-.env.prod}"

cd "$ROOT_DIR"

log() {
  printf '[deploy] %s\n' "$1"
}

fail() {
  printf '[deploy] ERROR: %s\n' "$1" >&2
  exit 1
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    fail "Missing required command: $command_name. Please install uv first (curl -LsSf https://astral.sh/uv/install.sh | sh)."
  fi
}

require_command uv

if [[ -f "$ENV_FILE" ]]; then
  log "Loading environment variables from $ENV_FILE"
  # Export env vars from file, ignoring comments
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Strip whitespace
    line=$(echo "$line" | xargs)
    if [[ -n "$line" && ! "$line" =~ ^# ]]; then
      export "$line"
    fi
  done < "$ENV_FILE"
else
  # If .env.prod doesn't exist, try copying .env.prod.example
  if [[ -f .env.prod.example ]]; then
    log "Copying .env.prod.example to .env.prod..."
    cp .env.prod.example .env.prod
    log "Created .env.prod. Please configure it and run deploy.sh again."
    exit 0
  else
    fail "Env file not found: $ENV_FILE"
  fi
fi

log "Syncing dependencies with uv..."
uv sync --frozen --no-dev

log "Running database migrations (Alembic)..."
uv run alembic upgrade head

log "Starting Mezon Bot natively..."
uv run python run.py --host 0.0.0.0 --port 8000
