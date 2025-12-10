#!/usr/bin/env bash
set -Eeuo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
BACKEND_DIR="${BACKEND_DIR:-$ROOT_DIR/backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
ENV_FILE="${ENV_FILE:-$BACKEND_DIR/.env}"

# ── Helpers ──────────────────────────────────────────────────────────────────
ip() { hostname -I | awk '{print $1}'; }

ensure_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Comando mancante: $1" >&2; exit 1;
  }
}

help() {
  cat <<EOF
Usage: ./run.sh <command>

Commands:
  install                 - uv sync (backend)
  run-api                 - avvia FastAPI (uvicorn) su 0.0.0.0:${BACKEND_PORT}
EOF
}

# ── Tasks ────────────────────────────────────────────────────────────────────
install() {
  ensure_cmd uv
  ( cd "$BACKEND_DIR" && uv sync )
}

run-api() {
  ensure_cmd uv
  ( cd "$BACKEND_DIR" && \
    uv run uvicorn app.main:app \
      --host 0.0.0.0 --port "${BACKEND_PORT}" \
      --env-file "${ENV_FILE}" --reload )
}

# ── Dispatcher ────────────────────────────────────────────────────────────────
main() {
  local cmd="${1:-help}"; shift || true
  local TIMEFORMAT=$'⏱  Task completed in %3lR'
  case "$cmd" in
    install|run-api|help)
      time "$cmd" "$@"
      ;;
    *)
      echo "Comando sconosciuto: $cmd"; echo; help; exit 1;;
  esac
}
main "$@"
