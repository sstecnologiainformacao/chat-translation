#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/services/backend"

echo "Repository: ${REPO_ROOT}"
echo "Backend: ${BACKEND_DIR}"

cd "${REPO_ROOT}"
echo
echo "== Git whitespace check =="
git diff --check

cd "${BACKEND_DIR}"
echo
echo "== Backend Python =="
uv run python --version

echo
echo "== Backend tests =="
uv run pytest -v

echo
echo "== Backend lint =="
uv run ruff check .

echo
echo "== Backend type check =="
uv run mypy

echo
echo "Backend checks completed."
