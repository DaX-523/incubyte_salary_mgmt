# Backend — Agent Guide

Repo-wide standards live in `../AGENTS.md`. This file adds the backend specifics.

## Stack

Python 3.13 · FastAPI · Pydantic 2 · uv (dependencies + venv) · pytest + pytest-cov · Ruff (lint +
format) · mypy (strict).

## Commands (run in `backend/`)

```sh
uv sync                 # install dependencies
uv run fastapi dev      # http://localhost:8000, OpenAPI docs at /docs
uv run pytest           # unit tests
uv run pytest --cov     # tests + 90% coverage gate
uv run ruff check --fix .
uv run ruff format .
uv run mypy
```

Full gate: `make check-backend` from the repo root. Add packages with `uv add <pkg>`
(`uv add --dev <pkg>` for tooling); never use pip or hand-edit `uv.lock`.

## Structure

```text
app/
  main.py        create_app(): wiring only (routers, middleware, exception handlers)
  api/           routers: parse request → call service → map result or error to HTTP
  schemas/       Pydantic request/response models (the API contract)
  services/      business logic: plain Python, no FastAPI imports
  repositories/  persistence behind small interfaces (once a database is added)
tests/           mirrors app/: app/services/payroll.py ↔ tests/services/test_payroll.py
  conftest.py    shared fixtures: `app` (fresh per test) and `client`
```

Create a directory when the first module needs it. Don't add empty layers.

## Writing code

- Route handlers stay thin. Business rules live in `services/` as plain functions or classes that
  take and return typed values, so they can be unit tested without HTTP.
- Declare dependencies (repositories, clock, settings) with `Annotated[..., Depends(...)]` so tests
  can swap them through `app.dependency_overrides`.
- Services raise domain exceptions (for example `EmployeeNotFoundError`). Only the API layer turns
  them into status codes.
- Every endpoint has typed request and response models. Don't return untyped dicts or ORM objects
  from business endpoints.
- Money is `Decimal`, never `float`. Quantize explicitly, with a named rounding mode.
- Configuration comes from the environment through a settings object. Never hard-code secrets.
- Type hints everywhere: mypy runs in strict mode and Ruff's rules are enforced.

## Writing tests

- Most tests are plain unit tests of services: no HTTP, no app. Use the `client` fixture to test
  the API contract: status codes, response bodies, validation errors (422) and error mapping
  (404, 409, …).
- Get the app only through the `app` and `client` fixtures (`create_app()` per test). Never import
  the module-level `app` into tests, because state would leak between tests.
- Replace collaborators with `app.dependency_overrides[...]` or by passing fakes into the service.
  Prefer simple in-memory fakes to `unittest.mock` chains, and never patch the unit under test.
- Table-drive edge cases with `@pytest.mark.parametrize(..., ids=[...])`, using ids that name each
  case.
- Fixtures belong in the nearest `conftest.py`. Keep them small and explicit, with no module-level
  mutable state.
- Control time by injecting a clock or a `today` parameter, not by patching `datetime`.
- pytest runs with `strict = true` and `filterwarnings = ["error"]`: unknown markers, config typos
  and warnings fail the run. Fix the cause instead of silencing the warning.
