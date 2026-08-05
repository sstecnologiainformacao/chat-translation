# Codex Handoff: Current Backend State

Date: 2026-07-29

## Purpose

This document lets a future Codex session resume the backend learning work without relying on chat history.

The active request before this update was to re-evaluate documentation after the OpenAI structured response work was merged into `main`.

## Required Reading Order

1. `AGENTS.md`
2. `services/backend/AGENTS.md`
3. `../chat-translation-docs/plans/python-chat-backend-plan.md`
4. This handoff document
5. Only the files needed for the next small backend step

Do not load broad unrelated documentation unless the current step requires it.

## Important Project Rules

- This is a local-only learning project. Do not suggest cloud services.
- All repository artifacts must be written in English.
- The learner may write prompts in English to practice.
- Codex should keep responding in Portuguese and include a brief English improvement note in every response.
- Codex may edit project files when explicitly asked, but learning-oriented backend work should still favor small objectives, review, checks, and explanation before broad implementation.
- New backend features must consider Pydantic at application boundaries: HTTP payloads, WebSocket payloads, settings, external API requests/responses, and JSON-shaped provider contracts.
- Pydantic should be adopted incrementally. Finish the current feature slice first, add Pydantic where it protects a real boundary, and avoid broad refactors mixed into unrelated feature work.

## Repository State

- Repository: `https://github.com/sstecnologiainformacao/chat-translation.git`
- Working tree path on the original Mac: `/Users/joaolucasdossantos/workspace-estudo/chat-translation`
- Active branch: `main`
- The previous OpenAI structured response branch was merged into `main`.
- The backend quality baseline is currently green:
  - `uv run pytest -q`: 66 tests passing
  - `uv run mypy app scripts`: passing
  - `uv run ruff check app scripts`: passing
  - `uv run ruff format --check app scripts`: passing

## Current Backend Focus

The current phase is the tail of Phase 9 from the active learning plan: translation abstraction and conversation context. Phase 10, the OpenAI translator, is implemented enough for local verification.

The confirmed design is:

- Public room context keys should look like `room:general`.
- Private chat context keys should look like `private:joao:maria`.
- Private chat participant names must be sorted when building the key.
- Each conversation keeps compact translation context.
- The translation provider receives one source message, all target languages, and the current compact context.
- The translation provider returns both `translations` and `context_update`.
- Conversation context should be updated only after translation succeeds.
- If translation fails, the message is not delivered and context is not updated.

## What Was Implemented So Far

Implemented:

- Auth, JWT, WebSocket routing, message schemas, public room messaging, and private messaging.
- Translation provider protocol and fake translator.
- Translation context and translation result shapes.
- Provider factory that returns `FakeTranslator` when `IS_DEVELOPMENT=true` and `OpenAITranslator` otherwise.
- `OpenAIClient` wrapper around the official OpenAI SDK.
- `OpenAITranslator` using Responses API structured parsing.
- Pydantic boundary models for OpenAI responses.
- Conversion from OpenAI list-shaped structured output into internal dictionary-shaped translation results.
- Manual real-API verification script at `services/backend/scripts/verify_openai_translation.py`.

Partially implemented:

- Conversation context is passed into translation calls.
- Private message flow applies the returned summary to its conversation context.
- Room message flow sends translations, but still needs explicit context update and recent-message tracking checks.

Not implemented yet:

- In-memory message repository and history retrieval.
- Complete recent-message accumulation in translation context for every successful message path.
- Tests proving room context updates only after successful translation.
- Tests proving failed translations do not mutate context.

## Current Known Failures

None at the quality baseline level.

Use this command set from `services/backend/`:

```bash
uv run pytest -q
uv run mypy app scripts
uv run ruff check app scripts
uv run ruff format --check app scripts
```

## Next Recommended Learning Step

Do not start a broad refactor yet.

Next objective for the learner:

1. Add focused tests around room conversation context updates.
2. Prove context is updated only after a successful room translation.
3. Prove failed translation does not mutate room context or deliver the message.
4. Then decide whether to clean up `Conversation.add_message` and recent message tracking before moving to in-memory history.

Suggested review target:

- `services/backend/app/services/chat.py`
- `services/backend/app/services/translation/base.py`
- `services/backend/app/tests/test_chat_service.py`

Suggested check after the learner changes Python:

```bash
cd services/backend
uv run pytest app/tests/test_chat_service.py -q
uv run mypy app/services/chat.py app/services/translation/base.py app/tests/test_chat_service.py
uv run ruff check app/services/chat.py app/services/translation/base.py app/tests/test_chat_service.py
```

## Guidance For The Next Codex Session

Default response style:

- Respond in Portuguese.
- Include a concise English improvement note in every response, either correcting the learner's wording or offering one practical tip.
- Keep all repository artifacts in English.
- Give findings first when reviewing code.
- Do not patch Python files unless the user explicitly asks to override the learning workflow.
- Give concepts, file pointers, behavior expectations, and commands.
- Provide exact Python only if the learner explicitly asks for it.

Useful current interpretation:

- The current direction is good and the quality baseline is green.
- The design should keep translation context independent enough that the provider does not need to import chat service internals.
- If a `Message` class remains in `translation/base.py`, consider whether it should be named specifically as a translation context message later.
- Keep the next step small: context update behavior is enough work for one checkpoint.
