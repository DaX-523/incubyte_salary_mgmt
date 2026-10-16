# Salary Management

Monorepo with a Next.js frontend and a FastAPI backend.

| Path        | Stack                                                               |
| ----------- | ------------------------------------------------------------------- |
| `frontend/` | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Vitest |
| `backend/`  | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, uv, pytest |

## Prerequisites

- Node.js 24 (`nvm use 24`; the version is pinned in `frontend/.nvmrc`)
- [uv](https://docs.astral.sh/uv/), which installs Python 3.13 automatically
- PostgreSQL, with two databases: one for development and one for tests
  (`createdb salary_mgmt && createdb salary_mgmt_test`)

## Getting started

```sh
cp backend/.env.example backend/.env   # then set DATABASE_URL and JWT_SECRET (openssl rand -hex 32)
make install
make dev-backend    # http://localhost:8000 (API docs at /docs); applies migrations on startup
make seed           # 10k demo employees with 12 months of payroll history, plus the demo login
make dev-frontend   # http://localhost:3000
```

`make seed` prints the demo login (`hr@acme.example`) with a newly generated password, once; it is
stored only as a hash. To get a new password without touching other data, run
`make seed args="--demo-login-only"`.

The frontend calls the API at `API_BASE_URL`, which defaults to `http://localhost:8000`. To point
it elsewhere, copy `frontend/.env.example` to `frontend/.env.local`.

## What it does

- **Login**: HR users log in with email and password. Each user belongs to an organization (the
  demo data is ACME) and only ever sees that organization's employees and payrolls. Logging out
  ends every session of that user.
- **Dashboard** (`/`): one month's payroll, defaulting to the current month. It shows a chart of
  paid vs total employees, then a collapsible filters panel (name, email, country, job title) and
  the employee list, 25, 50 or 100 rows per page. Salary sorting is available once a country is
  chosen.
- **Pay by job title** (`/insights`): headcount and salary range per job title within one country.
  "Rank by salary" opens that job title's peers sorted by pay, showing who is paid well above or
  below them.
- **Employees and payrolls**: add and edit employees, record and correct payrolls, and deactivate
  employees who leave (history is kept).

Salaries are in each country's local currency and are never converted, so pay is only compared
within a country.

Tests use `TEST_DATABASE_URL` (default `postgresql://localhost:5432/salary_mgmt_test`) and wipe it.

## Quality gates

```sh
make test     # fast unit tests for both apps
make check    # lint, formatting, type checks, and tests with a 90% coverage gate
```

Coding and testing standards for humans and AI agents are in [`AGENTS.md`](AGENTS.md), with
stack-specific rules in [`frontend/AGENTS.md`](frontend/AGENTS.md) and
[`backend/AGENTS.md`](backend/AGENTS.md).
