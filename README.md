# chat-translation

Project documentation lives outside this repository in `../chat-translation-docs/`.

Primary references:
- Project overview: `../chat-translation-docs/project-overview.md`
- Project structure: `../chat-translation-docs/project-structure.md`
- Architecture decisions: `../chat-translation-docs/decisions/`
- Specifications: `../chat-translation-docs/specifications/`
- Plans: `../chat-translation-docs/plans/`

## Local Docker Stack

Create local environment files:

```bash
./scripts/setup-env.sh
```

Then edit `environment/backend.env` and run:

```bash
docker compose up --build
```

The local stack starts:
- `postgres` for persistent local user storage.
- `migrations` for applying Alembic database migrations before the backend starts.
- `backend` for FastAPI and WebSocket chat.
- `frontend` for the Vite app.

PostgreSQL data is stored in the named Docker volume `chat-translation_postgres-data`.
