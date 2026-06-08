# AGENTS.md - frontend

Rules loaded when Codex touches `services/frontend/`. Universal rules live in the root `AGENTS.md`.

## Stack

- Vite + React 18 + TypeScript (strict mode).
- TailwindCSS (utility-first; no custom CSS unless necessary).
- shadcn/ui primitives in `src/components/ui/` (CLI-generated; never edit by hand).
- Vitest + React Testing Library for tests.
- `jwt-decode` for client-side JWT inspection (the server is the authority on validation).

## Folder conventions

- `src/features/<area>/` - screens, hooks, and components scoped to one feature. Co-located tests in `__tests__/`.
- `src/lib/` - non-UI helpers (API client, auth, generic hooks).
- `src/types/` - shared TS types. `messages.ts` mirrors the backend Pydantic schemas manually (see `../../../chat-translation-docs/decisions/0002-frontend-backend-types.md`).
- `src/components/ui/` - shadcn primitives. Never edit by hand; re-run `pnpm dlx shadcn@latest add <name>` to update.

## Size limits

- `.tsx` in `features/`: 500 lines or fewer.
- `.tsx` in `pages/`: 200 lines or fewer.
- Any other `.tsx`/`.ts`: 800 lines or fewer.

## Patterns

- No React Router in MVP. `App.tsx` switches via an `authenticated` flag.
- No Zustand/Redux in MVP. Plain `useState` + props local.
- WebSocket lives in `lib/useWebSocket.ts`; chat-specific orchestration in `features/chat/useChat.ts`.
- API base URL comes from `import.meta.env.VITE_API_URL` (default `http://localhost:8000`).

## Testing conventions

- Tests live in `__tests__/` next to the code under test.
- No tests for `useWebSocket` in MVP; add them in Cycle 2 once reconnection logic exists.
- Snapshot tests for layout are discouraged (brittle).

## Forbidden in frontend code

- Editing files inside `src/components/ui/` by hand.
- Adding state-management libraries before there is a proven need.
- Hard-coding the backend URL in components (use `lib/api.ts` and `useWebSocket`).
- Logging or alerting message content beyond toasts already specified in the spec.
