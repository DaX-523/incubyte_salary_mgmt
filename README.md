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
  chosen. **Download CSV** saves every employee the filters match (all pages, same order) as
  `employees-YYYY-MM.csv`. Text that Excel would run as a formula (starting with `=`, `+`, `-` or
  `@`) gets a leading `'`, so it shows as typed.
- **Pay insights** (`/insights`): per country, the headcount and the average and total monthly
  salary of active employees. Pick a country to see each job title's headcount and lowest,
  average and highest salary. "Rank by salary" opens that job title's peers sorted by pay,
  showing who is paid well above or below them.
- **Employees and payrolls**: add and edit employees, see each employee's payroll history, record
  and correct payrolls, and deactivate employees who leave (history is kept). An employee joins
  in the month they are added and can't be paid for an earlier month.

Salaries are in each country's local currency and are never converted, so pay is only compared
within a country, and there is no organization-wide total. Averages are rounded half up to the
cent.

## Not built yet

- **CSV import**, to move the existing spreadsheets in: validate the whole file with the API's
  schemas, then save every row or none and list the errors by row. It needs a real joining date
  on employees; today the month an employee is added counts as the month they joined.
- **Salary change history**: payrolls record what was paid each month, but not who changed a
  salary, or when.

Tests use `TEST_DATABASE_URL` (default `postgresql://localhost:5432/salary_mgmt_test`) and wipe it.

## Quality gates

```sh
make test     # fast unit tests for both apps
make check    # lint, formatting, type checks, and tests with a 90% coverage gate
```

GitHub Actions runs `make check` against a Postgres service on every push to `main` and every pull
request (`.github/workflows/check.yml`).

Coding and testing standards for humans and AI agents are in [`AGENTS.md`](AGENTS.md), with
stack-specific rules in [`frontend/AGENTS.md`](frontend/AGENTS.md) and
[`backend/AGENTS.md`](backend/AGENTS.md).

## Deploy

The frontend runs on Vercel, the API on Fly.io and the database on Supabase, all in Singapore:
every page makes a few API calls and each call makes a few queries, so the three sit together.
The browser only talks to the frontend, which calls the API from its server, so the API needs no
CORS.

1. **Database (Supabase).** Create a project in Southeast Asia (Singapore), then:
   - turn off the Data API (Integrations → Data API). The app reaches Postgres only through its
     own API, and the Data API could otherwise expose the tables the migrations create;
   - copy the **Session pooler** connection string (Connect → Session pooler) and add
     `?sslmode=require`. The direct connection is IPv6-only, and Fly's IPv6 route to Supabase has
     dropped connections before; the session pooler is IPv4 and behaves like a normal connection.

   On the free plan, a project with little activity for 7 days is paused until you restore it.

2. **API (Fly.io)**, from `backend/` (settings in `fly.toml`, image from `Dockerfile`):

   ```sh
   fly apps create salary-mgmt-api   # if the name is taken, pick another and update fly.toml
   fly secrets set DATABASE_URL='<session pooler URL>' JWT_SECRET="$(openssl rand -hex 32)"
   fly deploy
   curl https://salary-mgmt-api.fly.dev/health
   ```

   Migrations run when the API starts. Idle machines are suspended, costing storage only, and
   resume on the next request in under a second; the first request after a deploy waits for a
   normal start of a few seconds.

3. **Demo data**, once, from `backend/` on your machine. It prints the demo login:

   ```sh
   DATABASE_URL='<session pooler URL>' uv run python -m app.seed
   ```

4. **Frontend (Vercel).** Import the repository with Root Directory `frontend` and set
   `API_BASE_URL=https://salary-mgmt-api.fly.dev`. Its functions run in Singapore
   (`frontend/vercel.json`), and the session cookie is `Secure` in production.
