# Salary Management — Agent Guide

Monorepo with a Next.js frontend and a FastAPI backend. This file holds the repo-wide rules;
`frontend/AGENTS.md` and `backend/AGENTS.md` add stack-specific ones — read the one for the area
you are changing. Every `CLAUDE.md` just imports its sibling `AGENTS.md`, so edit `AGENTS.md`.

## Layout

| Path        | Stack                                                                     |
| ----------- | ------------------------------------------------------------------------- |
| `frontend/` | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, Vitest 5   |
| `backend/`  | Python 3.13, FastAPI, Pydantic 2, uv, pytest, Ruff, mypy                  |

## Commands (from repo root)

```sh
make install       # install both apps' dependencies
make dev-backend   # API on http://localhost:8000 (OpenAPI docs at /docs)
make dev-frontend  # web app on http://localhost:3000
make test          # all unit tests, fast feedback
make format        # auto-format and auto-fix lint in both apps
make check         # lint + format + types + tests with coverage gate, both apps
```

The frontend needs Node 24 (`nvm use 24`); uv manages Python for the backend.

## Engineering standards

Code is written to a high standard of quality **and** test coverage, on both the frontend and the
backend. These are requirements, not suggestions.

### Tests

- **Meaningful unit tests cover the core functionality.** Every behaviour change ships with its
  tests in the same change: business rules, calculations, validation, API contracts, and the UI
  behaviour users rely on. A bug fix starts with a failing test that reproduces the bug.
- **Fast.** Unit tests never touch a real network, real database or the real clock, and never
  sleep. The whole suite runs in seconds.
- **Deterministic.** Same result on every run, in any order, on any machine. Inject or freeze time,
  randomness, generated IDs, locale and timezone. No state shared between tests. A flaky test is a
  bug: fix it, never retry it.
- **Easy to understand.** One behaviour per test, named after that behaviour
  (`test_rejects_negative_salary`, `it("shows an error when salary is empty")`). Arrange–Act–Assert,
  separated by blank lines. Hard-code expected values instead of re-computing them with the logic
  under test. No loops or conditionals in a test body; use parametrization (`pytest.mark.parametrize`,
  `it.each`).
- **Edge cases, where they exist.** Boundaries (zero, negative, min/max, just over and under a
  limit), empty or missing input, invalid formats, rounding and precision, duplicates, not-found,
  and error paths. Table-drive them.
- **Test behaviour, not implementation.** Go through public interfaces: functions, HTTP endpoints,
  what the user sees. Mock only at system boundaries (HTTP, database, clock), never the unit under
  test.
- **Coverage gate: 90%** of lines, branches and functions per app, enforced by `make check`. It is
  a floor, not the goal; assertion-free tests written to move the number are not acceptable.

### Code structure, readability, maintainability

- Business logic lives in plain, framework-free functions and modules. Route handlers and React
  components are thin adapters around it. This is what keeps the core unit-testable.
- Small, single-purpose functions and modules. Intention-revealing names, no unexplained
  abbreviations.
- Strict typing everywhere: TypeScript `strict`, mypy `strict`. No `any`, `@ts-ignore`,
  `# type: ignore`, `# noqa` or `eslint-disable` without a comment saying why.
- Validate input at the boundary (Pydantic on the API, form validation in the UI), then trust the
  types inside.
- Handle errors explicitly and never swallow exceptions. Fail with a message that says what went
  wrong.
- No dead code, commented-out code, debug prints or magic numbers; name your constants.
- Prefer clarity over cleverness. Build for today's requirements and refactor when a real need
  arrives.
- Add a dependency only when it clearly earns its place.

### Domain: money

Salaries are money. Never use binary floats for amounts: use `Decimal` in Python, and decimal
strings or integer minor units (cents) on the wire and in the frontend. Make currency and rounding
rules explicit, and test them.

## Definition of done

1. Tests are added or updated for the change, including the relevant edge cases.
2. `make check` passes.
3. The diff has no unrelated changes and no leftover debug code.
