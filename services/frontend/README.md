# Frontend

React + Vite + TypeScript frontend for the local-only chat translation MVP.

The frontend is being built as a minimalist modern chat UI with shadcn/ui, TailwindCSS,
local JWT persistence, and public chat first.

## Requirements

- Node.js
- pnpm 9

Install dependencies from the repository root:

```bash
pnpm install
```

## Run Locally

From `services/frontend`:

```bash
pnpm dev
```

The app runs at:

```text
http://127.0.0.1:5173/
```

## Environment Variables

The frontend reads the backend URL from:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

If the variable is not set, the app defaults to `http://localhost:8000` for HTTP and
WebSocket clients.

## Docker

Build commands run from the repository root because the frontend is part of the pnpm
workspace and uses the root `pnpm-lock.yaml`.

Development image:

```bash
docker build -f services/frontend/Dockerfile.dev -t chat-translation-frontend-dev .
```

Production image:

```bash
docker build -f services/frontend/Dockerfile -t chat-translation-frontend .
```

## Quality Checks

From `services/frontend`:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

## Current Scope

Implemented:

- Vite + React + TypeScript scaffold.
- TailwindCSS v4.
- shadcn/ui baseline components.
- Vitest + React Testing Library setup.
- Playwright setup for browser-level checks.
- Login form wired to `POST /auth/login`.
- `sessionStorage` JWT persistence with client-side profile decoding.
- Frontend message types that mirror the backend WebSocket contracts.
- Public chat WebSocket hook and chat-specific orchestration.
- Public room message list, message composer, and connection state components.
- Frontend Dockerfiles for local dev and production-style builds.

Next:

- Validate the full frontend and backend flow locally with two browser sessions.
- Add private chat UI after the public flow is verified end to end.

Future UX backlog:

- Group consecutive messages from the same sender.
- Improve auto-scroll behavior.
- Show message sending and failure states.
- Improve the translated/original message display.
- Show message timestamps.
- Improve the empty chat state.
- Make missing or failed translations clearer to users.
- Polish dark mode, spacing, and chat bubble alignment.
- Distinguish the current user's messages from other users' messages.
- Evaluate WebSocket reconnection after the public MVP flow is stable.
- Evaluate optimistic message delivery with a translation loading state.
- Evaluate batched translation requests for multiple pending messages.
- Evaluate a background queue for translation work after the local MVP is stable.

## Architecture Notes

- `App.tsx` switches between authenticated and unauthenticated states in the MVP.
- No React Router, Zustand, or Redux in the MVP.
- Shared helpers belong in `src/lib/`.
- Feature-specific UI and hooks belong in `src/features/<area>/`.
- Backend message contracts are mirrored manually in `src/types/messages.ts`.
- shadcn/ui generated files live in `src/components/ui/` and should not be edited by hand.
