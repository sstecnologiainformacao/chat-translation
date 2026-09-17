#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
NGROK_API_URL="http://127.0.0.1:4040/api/tunnels"
NGROK_LOG="$(mktemp -t chat-translation-ngrok.XXXXXX)"
NGROK_PID=""

cleanup() {
  if [[ -n "${NGROK_PID}" ]] && kill -0 "${NGROK_PID}" 2>/dev/null; then
    kill "${NGROK_PID}" 2>/dev/null || true
    wait "${NGROK_PID}" 2>/dev/null || true
  fi
  rm -f "${NGROK_LOG}"
}

trap cleanup EXIT INT TERM

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
}

require_command curl
require_command docker
require_command ngrok
require_command python3

if [[ ! -f "${REPO_ROOT}/environment/backend.env" ]]; then
  echo "Missing environment/backend.env. Run ./scripts/setup-env.sh first." >&2
  exit 1
fi

if curl --silent --fail "${NGROK_API_URL}" >/dev/null 2>&1; then
  echo "Another ngrok agent is already using the local inspection API on port 4040." >&2
  echo "Stop it before running this script." >&2
  exit 1
fi

ngrok config check >/dev/null

echo "Starting ngrok for the frontend on port 5173..."
ngrok http 5173 --log stdout --log-format json >"${NGROK_LOG}" 2>&1 &
NGROK_PID=$!

PUBLIC_URL=""
for _ in {1..30}; do
  if ! kill -0 "${NGROK_PID}" 2>/dev/null; then
    echo "ngrok stopped before creating a tunnel:" >&2
    sed -n '1,120p' "${NGROK_LOG}" >&2
    exit 1
  fi

  PUBLIC_URL="$({ curl --silent --fail "${NGROK_API_URL}" 2>/dev/null || true; } | python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    print("")
else:
    urls = (
        tunnel.get("public_url", "")
        for tunnel in payload.get("tunnels", [])
    )
    print(next((url for url in urls if url.startswith("https://")), ""))
' 2>/dev/null)"

  if [[ -n "${PUBLIC_URL}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${PUBLIC_URL}" ]]; then
  echo "Timed out while waiting for the ngrok public URL:" >&2
  sed -n '1,120p' "${NGROK_LOG}" >&2
  exit 1
fi

ALLOWED_HOST="${PUBLIC_URL#https://}"
ALLOWED_HOST="${ALLOWED_HOST%%/*}"

echo
echo "Public application URL: ${PUBLIC_URL}"
echo "Keep this terminal open while other people use the application."
echo "Press Ctrl+C to stop Docker Compose and ngrok."
echo

cd "${REPO_ROOT}"
VITE_API_URL="${PUBLIC_URL}" \
VITE_ALLOWED_HOST="${ALLOWED_HOST}" \
  docker compose up --build
