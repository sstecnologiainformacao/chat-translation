#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="$ROOT_DIR/environment"

copy_if_missing() {
  local example="$1"
  local target="$2"

  if [ -f "$target" ]; then
    echo "exists: $target - skipping"
    return
  fi

  cp "$example" "$target"
  echo "created: $target"
  echo "  Edit it to fill in CHAT_PASSWORD, JWT_SECRET, and OPENAI_API_KEY."
}

copy_if_missing "$ENV_DIR/backend.env.example" "$ENV_DIR/backend.env"
