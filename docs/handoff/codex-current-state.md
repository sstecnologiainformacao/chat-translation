# Codex Handoff: Current Project State

Date: 2026-09-17

## Purpose

This document lets a future Codex session resume the current learning work without relying on chat
history. It is the most current checkpoint when older planning documents disagree with the code.

## Required Reading Order

1. `AGENTS.md`
2. The nested `AGENTS.md` for the area being changed
3. This handoff document
4. Only the files needed for the next small step

The detailed plans under `../chat-translation-docs/` contain useful history, but some active-step and
test-count sections are stale. Use the code and this handoff as the current operational state.

## Working Rules

- The project is local-only. Do not introduce cloud services or cloud-specific tooling.
- All repository artifacts must be written in English.
- Respond to the learner in Portuguese and include a brief English improvement note.
- For backend Python learning, give a small objective, concepts, file pointers, and expected
  behavior. Do not provide complete Python code unless the learner explicitly requests it.
- Codex may implement frontend React changes directly.
- Consider Pydantic for every new application boundary, but do not force it into internal domain
  objects where runtime validation or serialization is unnecessary.
- Keep changes small, test-focused, and consistent with the existing layers.

## Git State At Handoff

- Repository: `https://github.com/sstecnologiainformacao/chat-translation.git`
- Branch: `websocket-connection-limit`
- Branch base: commit `c1604ca` from `main`
- The connection-limit work is not committed yet.
- Modified implementation files:
  - `services/backend/app/main.py`
  - `services/backend/app/routers/websocket.py`
  - `services/backend/app/services/chat.py`
  - `services/backend/app/tests/test_chat_service.py`

Do not discard these learner-authored changes.

## Current Application State

The local stack runs with Docker Compose and contains:

- PostgreSQL for persistent user accounts.
- An Alembic migration service that runs before the backend.
- A FastAPI backend with registration, login, JWT authentication, and WebSocket chat.
- A React/Vite frontend with registration, login, public chat, private chat controls, language
  selection, dark mode, and session-scoped authentication storage.

Backend behavior already implemented:

- PostgreSQL-backed user registration and login through `SqlAlchemyUserRepository`.
- Dependency functions compose database sessions, repositories, and `AuthService`.
- Public and private messages with Pydantic WebSocket payload validation.
- Translation through a provider abstraction with fake and OpenAI implementations.
- OpenAI Responses API structured output parsed through Pydantic models.
- Per-conversation compact translation context.
- In-memory public and private message history.
- Public history translated for a newly joined user's language.
- Optimistic public-room delivery: the original message is broadcast first and a
  `room_translation_update` follows after translation finishes.
- A fixed supported-language list in the user flow, without country flags.

Known intentional limitations:

- Message history and translation context are lost when the backend restarts.
- There is no Redis, RabbitMQ, or background worker yet.
- Translation still runs inside the backend process.
- There is no automatic WebSocket reconnection.
- JWT expiration is checked at connection time, not again during an established WebSocket session.

## Active Work: WebSocket Capacity

The goal of the current branch is to begin protecting the app before testing 20 to 30 simultaneous
chat users.

Implemented but not committed:

- The production app creates `ConnectionManager(max_connections=30)`.
- `ConnectionManager.connect` raises `ConnectionLimitReachedError` when capacity is full.
- Rejected connections are not added to the manager.
- The WebSocket router catches that error and closes the connection with code `1008`.
- A service test proves that a second connection is rejected when a manager configured for one
  connection is already full, and that the connection count remains one.

Latest verified backend baseline after these changes:

- `uv run pytest -q`: 94 passed, 1 skipped.
- `uv run mypy app`: passed for 45 source files.
- `uv run ruff check app`: passed.
- `uv run ruff format --check app`: passed.

The skipped test is the opt-in real OpenAI integration test; automated checks must not require a
real API key.

## Exact Next Step

Add one focused test in `services/backend/app/tests/test_websocket.py` that verifies the router-level
capacity behavior:

1. Configure the app's `ChatService` with `ConnectionManager(max_connections=1)`.
2. Open and keep the first authenticated WebSocket connected.
3. Attempt a second authenticated WebSocket connection.
4. Assert that the second client receives WebSocket close code `1008`.
5. Ensure test setup does not leak the one-connection service into other tests.

This test is important because the existing service test proves the manager rule, but does not prove
that the WebSocket route translates the domain error into the expected protocol close behavior.

After that test passes, rerun the complete backend checks. Then commit this branch before starting
the next concurrency checkpoint.

## Following Checkpoint

After the connection-cap branch is merged, measure and reason about concurrent message translation.
The current async route can accept multiple connections, but translation latency, simultaneous API
calls, broadcast ordering, and failure isolation still need a deliberate test. Do not introduce
Redis or RabbitMQ before measuring the current behavior and defining the failure and ordering
requirements.

## Verification Commands

Run from `services/backend/`:

```bash
uv run pytest app/tests/test_chat_service.py app/tests/test_websocket.py -q
uv run pytest -q
uv run mypy app
uv run ruff check app
uv run ruff format --check app
```

Before committing, run from the repository root:

```bash
git diff --check
git status --short
```

## Suggested Resume Prompt

```text
Read AGENTS.md, services/backend/AGENTS.md, and docs/handoff/codex-current-state.md.
Continue from the exact next step without discarding the current branch changes.
Keep the guided Python learning workflow and respond in Portuguese with an English improvement note.
```
