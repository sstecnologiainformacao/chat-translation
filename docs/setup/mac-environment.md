# Mac Environment Setup

This guide recreates the local development environment for `chat-translation` on another Mac.

## Target Environment From The Original Mac

Observed environment:

- macOS: `26.2`
- Build: `25C56`
- CPU architecture: `arm64`
- Shell: `zsh 5.9`
- Git: `git version 2.50.1 (Apple Git-155)`
- Backend Python in project virtual environment: `3.11.15`
- Backend virtual environment path: `services/backend/.venv`
- Backend package manager: `uv`
- Backend lock file: `services/backend/uv.lock`
- Backend test tool: `pytest 9.0.3`
- Backend linter: `ruff 0.15.12`
- Backend type checker: `mypy 1.20.2`
- Root package manager declaration: `pnpm@9.0.0`

The Codex sandbox used during this handoff could not see some globally installed tools in its `PATH`, even though project checks through `uv run` worked. On a normal terminal, validate tools with:

```bash
command -v uv
command -v gh
command -v node
command -v pnpm
```

## Repository Layout Requirement

The main project expects the documentation repository to be next to it:

```text
workspace-estudo/
  chat-translation/
  chat-translation-docs/
```

Clone both repositories into the same parent directory.

```bash
mkdir -p ~/workspace-estudo
cd ~/workspace-estudo
git clone https://github.com/sstecnologiainformacao/chat-translation.git
```

If `chat-translation-docs` is available as a repository, clone it next to `chat-translation`.

Then enter the project:

```bash
cd ~/workspace-estudo/chat-translation
git checkout wip-translation-context-openai
```

## One-Time Mac Prerequisites

Install Xcode Command Line Tools:

```bash
xcode-select --install
```

Install Homebrew from the official site if it is missing:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon Macs, make sure Homebrew is in `PATH`:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

For persistence, add the Homebrew shellenv line to `~/.zprofile`.

## Automated Project Setup

From the repository root:

```bash
./scripts/setup-mac-environment.sh
```

The setup script:

- checks that the machine is macOS
- checks for Xcode Command Line Tools
- installs missing Homebrew packages when Homebrew is available
- prepares `pnpm@9.0.0` through Corepack
- installs Python `3.11.15` through `uv`
- runs `uv sync --python 3.11.15 --frozen` in `services/backend`
- runs `pnpm install` at the root when `pnpm` is available

## Environment Variables

Automated tests set their own values in `services/backend/app/tests/conftest.py`.

For manual backend runs, set these process environment variables:

```bash
export CHAT_USER="test-user"
export CHAT_PASSWORD="test-pass"
export JWT_SECRET="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
export JWT_EXPIRES_MINUTES="60"
export OPENAI_API_KEY="sk-your-local-key"
export OPENAI_MODEL="gpt-5.4-mini"
```

Never commit real secrets.

## Verification Commands

Check the local machine and project toolchain:

```bash
./scripts/check-local-environment.sh
```

Run backend checks:

```bash
./scripts/check-backend.sh
```

At the current handoff point, backend checks are expected to fail because the learner is in the middle of Phase 9 translation context work. See `docs/handoff/codex-current-state.md`.

## Manual Backend Commands

Start the backend locally:

```bash
cd services/backend
uv run uvicorn app.main:app --reload
```

Run one focused test:

```bash
cd services/backend
uv run pytest app/tests/test_chat_service.py::test_create_public_chat_context_key -q
```

Run all backend checks manually:

```bash
cd services/backend
uv run pytest -v
uv run ruff check .
uv run mypy
```

## GitHub CLI Setup

Install `gh` through the setup script or Homebrew:

```bash
brew install gh
```

Authenticate:

```bash
gh auth login
gh auth status
```

The project has previously used `gh` from the normal terminal for PR work. If Codex cannot see `gh`, check whether the shell profile loaded in Codex has the same `PATH` as the user's terminal.

## Troubleshooting

If `uv` is missing:

```bash
brew install uv
```

If Python is not `3.11.15` inside the backend environment:

```bash
cd services/backend
uv python install 3.11.15
uv sync --python 3.11.15 --frozen
uv run python --version
```

If `pnpm` is missing after Node is installed:

```bash
corepack enable
corepack prepare pnpm@9.0.0 --activate
pnpm --version
```

If `git diff --check` fails, fix whitespace before committing.

If tests fail during this handoff, check `docs/handoff/codex-current-state.md` before changing code. Some failures are expected because the current Python work is unfinished.
