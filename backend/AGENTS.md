# Backend — Agent Guide

Repo-wide standards live in `../AGENTS.md`. This file adds the backend specifics.

## Stack

Python 3.13 · FastAPI · Pydantic 2 · SQLAlchemy 2 (sync, psycopg 3) · Alembic · PostgreSQL ·
uv (dependencies + venv) · pytest + pytest-cov · Ruff (lint + format) · mypy (strict).

## Commands (run in `backend/`)

```sh
uv sync                                  # install dependencies
uv run fastapi dev                       # http://localhost:8000, docs at /docs; migrates on startup
uv run alembic upgrade head              # apply migrations without starting the API
uv run alembic revision --autogenerate -m "add x to y"   # new migration from model changes
uv run python -m app.seed [--reset]      # 10k employees + 12 months of payrolls (see --help)
uv run pytest                            # tests (integration tests skip without TEST_DATABASE_URL)
uv run pytest --cov                      # tests + 90% coverage gate
uv run ruff check --fix . && uv run ruff format .
uv run mypy
```

Full gate: `make check-backend` from the repo root (it sets `TEST_DATABASE_URL`). Add packages
with `uv add <pkg>` (`uv add --dev <pkg>` for tooling); never use pip or hand-edit `uv.lock`.

## Configuration

`app/core/config.py` reads settings from the environment and `backend/.env`
(template: `.env.example`). `DATABASE_URL` accepts plain `postgresql://` URLs; they are pointed at
the psycopg 3 driver automatically. When `DATABASE_URL` is set, the API applies pending migrations
on startup (serialized with a Postgres advisory lock); when unset, it starts without a database.

## Structure

```text
app/
  main.py        create_app(): wiring only (routers under /api/v1, lifespan, error handlers)
  core/          settings
  domain/        catalog.py (countries → currency, job titles → department), errors.py
  api/           routers: parse request → call service → map result or error to HTTP
  schemas/       Pydantic request/response models (the API contract)
  services/      business logic: plain Python, no FastAPI imports
  repositories/  SQL behind small Protocols; tests swap in the fakes from tests/fakes.py
  db/            SQLAlchemy models (models.py), metadata (base.py), migration runner (migrate.py)
  seed/          demo data: pure generator, database writer, CLI (`python -m app.seed`)
migrations/      Alembic environment and versions/
tests/           mirrors app/: app/services/payroll.py ↔ tests/services/test_payroll.py
  conftest.py    shared fixtures: `app`, `client` and the in-memory repositories
  api/           contract tests; `api_client` serves the in-memory repositories
  integration/   tests against a real Postgres (TEST_DATABASE_URL)
```

Create a directory when the first module needs it. Don't add empty layers.

## Data model and migrations

- `app/db/models.py` is the source of truth for the schema; every change ships with a migration.
  Generate it with `--autogenerate`, then read and fix it: autogenerate misses CHECK constraints
  and renames. `test_migrated_schema_matches_the_models` fails if models and migrations drift.
- Never edit a migration that has been applied anywhere; add a new one. Every migration has a
  working `downgrade()`.
- Migrations must not import application code. Freeze values they depend on (see
  `PAYMENT_METHODS` in the migrations) so old migrations keep working as the app changes.
- Enforce invariants in the database too: NOT NULL, CHECKs, foreign keys, and
  `UNIQUE (employee_id, month)` on payrolls. Constraint names come from the naming convention in
  `app/db/base.py`; keep them that way so migrations can refer to them.
- Money columns are `Numeric(14, 2)` mapped to `Decimal`. Countries are ISO 3166-1 alpha-2 codes,
  currencies ISO 4217 codes, months are stored as the first day of the month.
- `employees.monthly_salary` is in the country's local currency; there is deliberately no salary
  currency column and no conversion. Pay queries group or filter by `country` first (peers =
  same `country` and `job_title`), which is what the `country`, `department` and `job_title`
  indexes serve. There is no salary filter.
- Store facts once. Don't add columns that can be derived from other tables (the removed
  `last_transaction_at` was the latest payroll's `created_at`).

## The API

Everything lives under `/api/v1` (OpenAPI docs at `/docs`). Domain errors map to HTTP in
`app/api/errors.py`: `NotFoundError` → 404, `ConflictError` → 409; request validation is 422.

- Money goes over the wire as decimal strings with two places (`"4780.00"`); months as `YYYY-MM`.
- Clients send catalog values (country, job title) and the server derives the rest: department
  from job title, currency from country. Request models use `extra="forbid"`, so a client can't
  set a derived or fixed field (`department`, `currency`, a payroll's `month`, an employee's
  `country`).
- `DELETE /employees/{id}` deactivates; nothing is ever deleted, and inactive employees can't get
  new payrolls.
- "On the books for a month" (`app/repositories/population.py`) is shared by the monthly list
  and the paid-vs-total insight, so the two always agree.

## Writing code

- Route handlers stay thin. Business rules live in `services/` as plain functions or classes that
  take and return typed values, so they can be unit tested without HTTP.
- Declare dependencies (sessions, repositories, clock, settings) with `Annotated[..., Depends(...)]`
  so tests can swap them through `app.dependency_overrides`.
- Services raise domain exceptions (for example `EmployeeNotFoundError`). Only the API layer turns
  them into status codes.
- Every endpoint has typed request and response models. Don't return untyped dicts or ORM objects
  from business endpoints.
- List endpoints filter and paginate in SQL, never in Python, and use the indexed columns.
- Money is `Decimal`, never `float`. Quantize explicitly, with a named rounding mode.
- Never hard-code secrets or connection strings; read them from settings.
- Type hints everywhere: mypy runs in strict mode and Ruff's rules are enforced.

## Writing tests

- Most tests are plain unit tests of services and pure functions: no HTTP, no database. Use the
  `client` fixture to test the API contract: status codes, response bodies, validation errors
  (422) and error mapping (404, 409, …).
- Get the app only through the `app` and `client` fixtures. They build it with explicit settings
  (no `.env`, no database), so state never leaks between tests and nothing touches real data.
- Database behaviour (constraints, migrations, queries, repositories) is tested in
  `tests/integration/` with the `engine` fixture, which truncates tables after each test. These
  tests skip when `TEST_DATABASE_URL` is unset; `make check` sets it.
- Replace collaborators with `app.dependency_overrides[...]` or by passing fakes into the service.
  Prefer simple in-memory fakes to `unittest.mock` chains, and never patch the unit under test.
- Table-drive edge cases with `@pytest.mark.parametrize(..., ids=[...])`, using ids that name each
  case.
- Fixtures belong in the nearest `conftest.py`. Keep them small and explicit, with no module-level
  mutable state.
- Control time and randomness by passing them in (a `today` parameter, a seeded `Random`), not by
  patching `datetime` or `random`.
- pytest runs with `strict = true` and `filterwarnings = ["error"]`: unknown markers, config typos
  and warnings fail the run. Fix the cause instead of silencing the warning.
