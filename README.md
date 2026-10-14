# Salary Management

Monorepo with a Next.js frontend and a FastAPI backend.

| Path        | Stack                                                                |
| ----------- | -------------------------------------------------------------------- |
| `frontend/` | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Vitest  |
| `backend/`  | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, uv, pytest  |

## Prerequisites

- Node.js 24 (`nvm use 24`; the version is pinned in `frontend/.nvmrc`)
- [uv](https://docs.astral.sh/uv/), which installs Python 3.13 automatically
- PostgreSQL, with two databases: one for development and one for tests
  (`createdb salary_mgmt && createdb salary_mgmt_test`)

## Getting started

```sh
cp backend/.env.example backend/.env   # then set DATABASE_URL
make install
make dev-backend    # http://localhost:8000 (API docs at /docs); applies migrations on startup
make seed           # 10k demo employees with 12 months of payroll history
make dev-frontend   # http://localhost:3000
```

Tests use `TEST_DATABASE_URL` (default `postgresql://localhost:5432/salary_mgmt_test`) and wipe it.

## Quality gates

```sh
make test     # fast unit tests for both apps
make check    # lint, formatting, type checks, and tests with a 90% coverage gate
```

Coding and testing standards for humans and AI agents are in [`AGENTS.md`](AGENTS.md), with
stack-specific rules in [`frontend/AGENTS.md`](frontend/AGENTS.md) and
[`backend/AGENTS.md`](backend/AGENTS.md).
