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

If the variable is not set, the app should default to `http://localhost:8000` when API and
WebSocket clients are implemented.

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
- Initial app shell with login form and public room preview.

Next:

- Add frontend types that mirror the backend Pydantic message schemas.
- Add `lib/api.ts` for `POST /auth/login`.
- Add `lib/auth.ts` for `localStorage` token persistence.
- Connect the public chat WebSocket flow.

## Architecture Notes

- `App.tsx` switches between authenticated and unauthenticated states in the MVP.
- No React Router, Zustand, or Redux in the MVP.
- Shared helpers belong in `src/lib/`.
- Feature-specific UI and hooks belong in `src/features/<area>/`.
- Backend message contracts are mirrored manually in `src/types/messages.ts`.
- shadcn/ui generated files live in `src/components/ui/` and should not be edited by hand.
