# Backend

FastAPI backend for the local-only chat translation MVP.

The service provides:
- `POST /auth/login` for shared local authentication.
- `GET /health` for a simple health check.
- `WS /ws/chat` for authenticated public and private chat messages.
- Translation through a `TranslationProvider` abstraction.
- In-memory message history for the MVP.

Additional backend documentation lives at `../../../chat-translation-docs/backend/backend-overview.md`.

## Requirements

- Python 3.11
- `uv`

Install dependencies:

```bash
uv sync --dev
```

## Environment Variables

The backend reads settings from process environment variables. Python code does not load `.env`
files directly, so source the file in the shell before running commands.

Required variables:

| Variable | Required | Default | Description |
|---|---:|---|---|
| `CHAT_USER` | Yes | none | Shared local login username. |
| `CHAT_PASSWORD` | Yes | none | Shared local login password. |
| `JWT_SECRET` | Yes | none | HS256 signing secret. Use at least 32 characters. |
| `OPENAI_API_KEY` | Yes | none | OpenAI API key. A placeholder is enough when `IS_DEVELOPMENT=true`. |
| `IS_DEVELOPMENT` | Yes | none | `true` uses `FakeTranslator`; `false` uses `OpenAITranslator`. |
| `JWT_EXPIRES_MINUTES` | No | `60` | JWT lifetime in minutes. |
| `OPENAI_MODEL` | No | `gpt-5.4-mini` | Model used by the OpenAI translation provider. |

Example local `.env`:

```bash
CHAT_USER=local-user
CHAT_PASSWORD=local-pass
JWT_SECRET=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
JWT_EXPIRES_MINUTES=60
OPENAI_API_KEY=sk-local-placeholder
OPENAI_MODEL=gpt-5.4-mini
IS_DEVELOPMENT=true
```

Never commit real secrets.

## Run Locally

From `services/backend`:

```bash
set -a
source .env
set +a
uv run uvicorn app.main:app --reload
```

The API runs at:

- Health check: `http://127.0.0.1:8000/health`
- API docs: `http://127.0.0.1:8000/docs`

## Quality Checks

From `services/backend`:

```bash
uv run pytest -v
uv run ruff check .
uv run mypy
```

Useful focused checks:

```bash
uv run pytest app/tests/test_chat_service.py -q
uv run pytest app/tests/test_message_repository.py -q
uv run ruff format --check app scripts
```

Tool purpose:

- `pytest` validates runtime behavior through automated tests.
- `ruff check` validates lint rules and common Python quality issues.
- `ruff format --check` verifies formatting without changing files.
- `mypy` validates static typing expectations before runtime.

Automated tests set their own environment variables in `app/tests/conftest.py`.

## Login Flow

Request a JWT:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "local-user",
    "password": "local-pass",
    "nickname": "joao",
    "language": "Portuguese"
  }'
```

Successful response:

```json
{
  "token": "<jwt>"
}
```

Invalid credentials return `401` with `invalid_credentials`.

## WebSocket Flow

Connect to:

```text
ws://127.0.0.1:8000/ws/chat?token=<jwt>
```

The token is validated during the WebSocket handshake. Missing or invalid tokens are rejected with
close code `1008`.

The backend automatically joins authenticated users to the fixed public room named `general`.

Public room message:

```json
{
  "type": "room_message",
  "room": "general",
  "text": "Hello"
}
```

Private message:

```json
{
  "type": "private_message",
  "recipient_nickname": "maria",
  "text": "Hello"
}
```

Malformed payloads return:

```json
{
  "type": "error",
  "reason": "malformed_payload"
}
```

If a private recipient is not connected, the sender receives:

```json
{
  "type": "error",
  "reason": "recipient_not_found"
}
```

Successful room messages are broadcast as `room_message` payloads. When a user joins a room with
stored messages, the user receives a `room_history` payload with recent in-memory messages.

## Translation Provider

Provider creation is centralized in `app/services/translation/factory.py`.

- `IS_DEVELOPMENT=true` returns `FakeTranslator`.
- `IS_DEVELOPMENT=false` returns `OpenAITranslator`.

Automated tests must not call the real OpenAI API. They use fakes instead.

To manually verify the real OpenAI provider:

```bash
set -a
source .env
set +a
uv run python -m scripts.verify_openai_translation
```

For real OpenAI verification, set:

```bash
IS_DEVELOPMENT=false
OPENAI_API_KEY=<real-api-key>
```

## In-Memory History

The MVP uses `InMemoryMessageRepository`.

Behavior:
- Successful public room messages are stored in memory.
- Successful private messages are stored in memory.
- Failed translations are discarded from history.
- New public room participants receive recent room history.
- Server restarts clear all history by design.

Permanent history is deferred to a later cycle.

## Backend Layout

See `AGENTS.md` for the full backend layering rules.

Current structure:

- `app/routers/`: HTTP and WebSocket entry points.
- `app/services/`: business logic and provider orchestration.
- `app/repositories/`: storage protocols and implementations.
- `app/schemas/`: Pydantic request and response models.
- `app/core/`: configuration and security helpers.
- `app/tests/`: automated tests.
- `scripts/`: manual verification scripts.

New backend features must consider whether Pydantic belongs at their input, output,
configuration, or external-provider boundary.
