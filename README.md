# Salary Management

Monorepo with a Next.js frontend and a FastAPI backend.

| Path        | Stack                                                       |
| ----------- | ----------------------------------------------------------- |
| `frontend/` | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Vitest    |
| `backend/`  | Python 3.13, FastAPI, Pydantic 2, uv, pytest, Ruff, mypy    |

## Prerequisites

- Node.js 24 (`nvm use 24`; the version is pinned in `frontend/.nvmrc`)
- [uv](https://docs.astral.sh/uv/), which installs Python 3.13 automatically

## Getting started

```sh
make install
make dev-backend    # http://localhost:8000 (API docs at /docs)
make dev-frontend   # http://localhost:3000
```

## Quality gates

```sh
make test     # fast unit tests for both apps
make check    # lint, formatting, type checks, and tests with a 90% coverage gate
```

Coding and testing standards for humans and AI agents are in [`AGENTS.md`](AGENTS.md), with
stack-specific rules in [`frontend/AGENTS.md`](frontend/AGENTS.md) and
[`backend/AGENTS.md`](backend/AGENTS.md).
