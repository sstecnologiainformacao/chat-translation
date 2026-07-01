#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/services/backend"
REQUIRED_PYTHON="3.11.15"
REQUIRED_PNPM="9.0.0"

section() {
  echo
  echo "== $1 =="
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

install_with_brew_if_missing() {
  local package="$1"
  local command_name="$2"

  if has_command "${command_name}"; then
    echo "${command_name} already exists at $(command -v "${command_name}")"
    return
  fi

  if ! has_command brew; then
    echo "Homebrew is required to install ${package} automatically."
    echo "Install Homebrew from https://brew.sh and re-run this script."
    exit 1
  fi

  brew install "${package}"
}

section "System checks"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup script is for macOS only."
  exit 1
fi

echo "macOS:"
sw_vers
echo "Architecture: $(uname -m)"

if ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools are missing."
  echo "Run: xcode-select --install"
  exit 1
fi

section "Tool installation"
install_with_brew_if_missing uv uv
install_with_brew_if_missing gh gh
install_with_brew_if_missing node node

section "pnpm"
if has_command corepack; then
  corepack enable
  corepack prepare "pnpm@${REQUIRED_PNPM}" --activate
else
  echo "corepack is missing. It should be available after Node is installed."
  exit 1
fi

pnpm --version

section "Backend Python"
cd "${BACKEND_DIR}"
uv python install "${REQUIRED_PYTHON}"
uv sync --python "${REQUIRED_PYTHON}" --frozen
uv run python --version

section "Root JavaScript dependencies"
cd "${REPO_ROOT}"
pnpm install

section "Done"
echo "Setup completed."
echo "Next checks:"
echo "  ./scripts/check-local-environment.sh"
echo "  ./scripts/check-backend.sh"
