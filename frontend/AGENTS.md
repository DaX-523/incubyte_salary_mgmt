<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Frontend — Agent Guide

Repo-wide standards live in `../AGENTS.md`. This file adds the frontend specifics. The block above
is managed by Next.js: leave it in place.

## Stack

Next.js 16 (App Router, `src/` dir) · React 19 · TypeScript (strict) · Tailwind CSS 4 · ESLint +
Prettier · Vitest 5 + React Testing Library (jsdom). Node 24 (`nvm use`).

## Commands (run in `frontend/`)

```sh
npm run dev            # http://localhost:3000
npm test               # unit tests, single run
npm run test:watch     # tests in watch mode
npm run test:coverage  # tests + 90% coverage gate
npm run lint
npm run typecheck
npm run format
npm run check          # lint + format check + typecheck + coverage; must pass
```

## Structure

```text
src/
  app/         routes, layouts, pages: thin, they compose components and load data
  components/  reusable UI components
  lib/         framework-free logic: formatting, validation, calculations, API client
```

Tests sit next to the code they test: `money.ts` → `money.test.ts`, `SalaryForm.tsx` →
`SalaryForm.test.tsx`. Import through the `@/` alias (`@/lib/money`), not long relative paths.

## Writing code

- Use Server Components by default. Add `"use client"` only for state, effects, event handlers or
  browser APIs, and place it as low in the tree as possible.
- Keep logic out of components. Compute in `src/lib/` and unit test it there; components render
  and wire up events.
- Type props explicitly and never use `any`. Define API request and response types once, in the API
  client, rather than ad hoc in each component.
- Make components accessible by default: semantic elements, labelled form controls, `<button>` for
  actions. The tests below depend on it.
- Style with Tailwind utility classes.

## Writing tests

- Test what the user sees and does. Query by role, label or text
  (`screen.getByRole("button", { name: "Save" })`); `getByTestId` is a last resort.
- Simulate interaction with `@testing-library/user-event` (`const user = userEvent.setup()`), not
  `fireEvent`.
- Assert with jest-dom matchers: `toBeInTheDocument`, `toHaveValue`, `toBeDisabled`, and so on.
- Never use the real network. Mock the API client module (`vi.mock("@/lib/api")`) or stub `fetch`
  with `vi.stubGlobal`. Spies, stubbed globals and env vars are restored automatically between
  tests.
- For time-dependent code, use `vi.useFakeTimers()` with `vi.setSystemTime(...)`, and call
  `vi.useRealTimers()` in `afterEach`.
- Wait for async UI with `findBy*` or `waitFor`, never with arbitrary delays.
- Vitest cannot render `async` Server Components. Keep them thin (load data, pass props) and test
  the logic and the presentational components they render.
- `layout.tsx` files are excluded from coverage, so they must stay free of logic.
