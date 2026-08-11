# AGENTS.md - frontend

Rules loaded when Codex touches `services/frontend/`. Universal rules live in the root `AGENTS.md`.

## Working mode

- Frontend work is vibe-coding oriented: Codex may implement in-scope frontend changes directly when asked to build, change, fix, scaffold, or polish.
- For review, planning, or diagnosis requests, inspect the relevant files and report findings before changing code.
- Ask before external writes, destructive actions, dependency choices that materially change the stack, or scope expansion beyond the frontend MVP.
- Keep implementation slices small enough to review, run checks, and commit independently.
- Explain meaningful product, design, and architecture decisions briefly after implementation.

## Stack

- Vite + React 18 + TypeScript (strict mode).
- TailwindCSS (utility-first; no custom CSS unless necessary).
- shadcn/ui primitives in `src/components/ui/` (CLI-generated; never edit by hand).
- Vitest + React Testing Library for tests.
- Playwright for browser-level checks and visual interaction validation.
- `jwt-decode` for client-side JWT inspection (the server is the authority on validation).

## Product decisions

- Build a minimalist modern chat interface.
- Keep colors and visual style easy to change through theme tokens and shared styling conventions.
- All UI text, file names, identifiers, comments, and tests are written in English.
- Store the JWT in `localStorage` for MVP session persistence.
- Let users type their preferred language freely; do not force a fixed language list.
- Public chat comes first. Private chat UI is deferred until the public flow is complete.
- Render the translated text as the primary message content and the original text as secondary context.
- The first screen is the usable app experience, not a marketing landing page.

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
- HTTP login lives in `lib/api.ts`.
- JWT storage helpers live in `lib/auth.ts`.
- Backend WebSocket URL is derived from `VITE_API_URL`; do not duplicate URL-building logic in components.
- Components should receive typed props and avoid reaching into `localStorage`, `fetch`, or `WebSocket` directly.

## Design conventions

- Use shadcn/ui for common primitives such as buttons, inputs, labels, textareas, scroll areas, and dialogs.
- Do not edit generated shadcn/ui files by hand.
- Prefer Tailwind utility classes plus CSS variables/theme tokens over ad hoc inline styles.
- Keep the chat interface dense enough for daily use: clear message list, composer, connection state, and sign-out action.
- Include loading, error, empty, connecting, open, and closed states where the user would naturally expect them.
- Use responsive layout constraints so text, controls, and message bubbles do not overlap on mobile or desktop.

## Testing conventions

- Tests live in `__tests__/` next to the code under test.
- Add unit tests for new non-trivial helpers, hooks, and components.
- Prefer behavior tests over implementation-detail tests.
- Mock network boundaries for `fetch`, `localStorage`, and `WebSocket`.
- Keep WebSocket reconnection tests out of the MVP unless reconnection logic is added.
- Use Playwright for critical user flows that need a real browser.
- Snapshot tests for layout are discouraged (brittle).

## Validation

- After frontend implementation, run the relevant package checks from `services/frontend`.
- Expected checks once scaffolded: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm test:e2e`, and `pnpm build`.
- For UI work, run the dev server and inspect the actual app in browser-sized viewports before calling the work done.

## Forbidden in frontend code

- Editing files inside `src/components/ui/` by hand.
- Adding state-management libraries before there is a proven need.
- Hard-coding the backend URL in components (use `lib/api.ts` and `useWebSocket`).
- Logging or alerting message content beyond toasts already specified in the spec.
