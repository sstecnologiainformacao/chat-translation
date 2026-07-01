#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/services/backend"
EXPECTED_BACKEND_PYTHON="Python 3.11.15"
EXPECTED_PNPM="9.0.0"

status=0

section() {
  echo
  echo "== $1 =="
}

require_command() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "missing: ${name}"
    status=1
    return 1
  fi

  echo "${name}: $(command -v "${name}")"
  return 0
}

section "System"
sw_vers || status=1
echo "Architecture: $(uname -m)"
zsh --version || status=1

section "Global tools"
require_command git && git --version
require_command uv && uv --version
require_command gh && gh --version | head -n 1
require_command node && node --version
require_command pnpm && {
  actual_pnpm="$(pnpm --version)"
  echo "pnpm: ${actual_pnpm}"
  if [[ "${actual_pnpm}" != "${EXPECTED_PNPM}" ]]; then
    echo "expected pnpm ${EXPECTED_PNPM}"
    status=1
  fi
}

section "Repository"
cd "${REPO_ROOT}"
git status --short --branch

section "Backend environment"
cd "${BACKEND_DIR}"
if command -v uv >/dev/null 2>&1; then
  backend_python="$(uv run python --version)"
  echo "backend python: ${backend_python}"
  if [[ "${backend_python}" != "${EXPECTED_BACKEND_PYTHON}" ]]; then
    echo "expected ${EXPECTED_BACKEND_PYTHON}"
    status=1
  fi

  uv run pytest --version
  uv run ruff --version
  uv run mypy --version
else
  echo "cannot check backend because uv is missing"
  status=1
fi

section "Result"
if [[ "${status}" -eq 0 ]]; then
  echo "Local environment matches the expected project baseline."
else
  echo "Local environment has differences. See messages above."
fi

exit "${status}"
