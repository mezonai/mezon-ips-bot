#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-120}"
POLL_INTERVAL_SECONDS=5

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
    fail "Missing required command: $command_name"
  fi
}

docker_compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_for_app_health() {
  local container_id
  local deadline
  local status

  container_id="$(docker_compose ps -q app)"
  if [[ -z "$container_id" ]]; then
    fail "App container was not created"
  fi

  deadline=$((SECONDS + WAIT_TIMEOUT_SECONDS))
  while (( SECONDS < deadline )); do
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
    case "$status" in
      healthy)
        log "App container is healthy"
        return 0
        ;;
      running|starting)
        log "Waiting for app health: $status"
        sleep "$POLL_INTERVAL_SECONDS"
        ;;
      *)
        docker_compose logs --tail=100 app || true
        fail "App container is not healthy (status: $status)"
        ;;
    esac
  done

  docker_compose logs --tail=100 app || true
  fail "Timed out after ${WAIT_TIMEOUT_SECONDS}s waiting for app health"
}

require_command docker

if ! docker compose version >/dev/null 2>&1; then
  fail "Docker Compose v2 is required"
fi

[[ -f "$COMPOSE_FILE" ]] || fail "Compose file not found: $COMPOSE_FILE"
[[ -f "$ENV_FILE" ]] || fail "Env file not found: $ENV_FILE. Copy .env.prod.example to .env.prod and fill in real values."

log "Validating compose configuration"
docker_compose config >/dev/null

log "Pulling latest images"
docker_compose pull

log "Starting services"
docker_compose up -d --remove-orphans

wait_for_app_health

log "Current service status"
docker_compose ps
