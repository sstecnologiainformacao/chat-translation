# AGENTS.md (root)

This file is the entry point for Codex working on `chat-translation`. Keep it small; area-specific rules live in nested `AGENTS.md` files.

## Project context

`chat-translation` is a local-only learning project: a chat where users speaking different languages communicate, with translations produced by the OpenAI API. The two deployable units are the **frontend** (React + Vite + TS) and the **backend** (FastAPI + Python 3.11). Everything runs locally via Docker Compose.

## Permanent project policies

1. **No cloud, ever.** This project does not involve Azure, AWS, GCP, Terraform, Functions, Container App Jobs, or any cloud-specific tooling. Reject suggestions that require any of these. Codified in `../chat-translation-docs/decisions/0004-local-only-policy.md`.
2. **All artifacts in English.** Every Markdown, code file, comment, log message, identifier, and commit message is written in English regardless of the conversation language. Codified in `../chat-translation-docs/decisions/0006-english-only-artifacts.md`.
3. **Keep edits scoped and direct.** Codex may edit project files when asked, including Python files, but changes should follow the existing structure and be explained clearly.
4. **`AGENTS.md` is split by area.** This root file holds only universal rules; subdirectory rules live in nested `AGENTS.md` files. Codified in `../chat-translation-docs/decisions/0007-agent-instructions.md`.

## Source of truth

The structural contract is `../chat-translation-docs/project-structure.md`. If reality and the template disagree, fix the divergence or amend the template. Never tolerate silent drift.

## Branch to environment mapping

| Branch | Environment |
|---|---|
| `main` | Production-equivalent (no auto-deploy in MVP) |
| `staging` | Reserved for staging (no auto-deploy in MVP) |
| `dev/<name>/...` | Per-developer / per-feature sandbox |

## Pointers

- Backend (FastAPI, layering, testing): `services/backend/AGENTS.md`
- Frontend (Vite, shadcn/ui, file-size limits): `services/frontend/AGENTS.md`
- ADRs (template, naming, statuses): `../chat-translation-docs/agent-guidelines/architecture-decision-guidelines.md`

## GitHub workflow notes

- The GitHub CLI is available at `/opt/homebrew/bin/gh`; Codex's default `PATH` may not include Homebrew.
- If `gh` cannot reach `api.github.com` from the sandbox, retry the same command with escalated network permission.

## Forbidden anti-patterns

Loose Markdown at the root unless it is project metadata (`README.md`, `PROJECT_STRUCTURE_TEMPLATE.md`, `AGENTS.md`); committed `node_modules/`, `.venv/`, `__pycache__/`; logs (`*.log`), backups (`*.bak`, `*.old`), dumps (`*.dump`); copy-pasted code between services; `:latest` Docker tags; per-service IaC; per-environment shared Terraform state.
