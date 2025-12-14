#!/usr/bin/env bash
# Export env vars from project .env and run the DB connection test script
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
SCRIPT="$ROOT_DIR/db/db_connection_test.py"

if [ ! -f "$ENV_FILE" ]; then
  echo "No $ENV_FILE found at project root. Create it or copy from example."
  exit 1
fi

echo "Exporting environment variables from $ENV_FILE"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ ! -f "$SCRIPT" ]; then
  echo "Test script not found: $SCRIPT" >&2
  exit 1
fi

echo "Running DB connection test script: $SCRIPT"
python3 "$SCRIPT"
