# Developer entry points for the monorepo. Run `make` to list targets.
.DEFAULT_GOAL := help
NODE_MAJOR := 24
# Integration tests run against this database and wipe it; never point it at real data.
TEST_DATABASE_URL ?= postgresql://localhost:5432/salary_mgmt_test
export TEST_DATABASE_URL

.PHONY: help install dev-backend dev-frontend migrate migration seed test format check check-backend check-frontend require-node

help: ## List available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-15s %s\n", $$1, $$2}'

install: require-node ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm install

dev-backend: ## Run the API with auto-reload on http://localhost:8000
	cd backend && uv run fastapi dev

dev-frontend: require-node ## Run the web app on http://localhost:3000
	cd frontend && npm run dev

migrate: ## Apply pending migrations to DATABASE_URL (the API also does this on startup)
	cd backend && uv run alembic upgrade head

migration: ## Generate a migration from model changes: make migration name="add x to y"
	@test -n "$(name)" || { echo 'Usage: make migration name="describe the change"'; exit 1; }
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

seed: ## Seed 10k demo employees, payroll history and the demo login (args="--reset" replaces data)
	cd backend && uv run python -m app.seed $(args)

test: require-node ## Run all tests (no coverage, fast feedback)
	cd backend && uv run pytest
	cd frontend && npm test

format: require-node ## Auto-format and auto-fix lint issues in both apps
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && npm run format && npm run lint -- --fix

check: check-backend check-frontend ## Full quality gate for both apps (must pass before done)

check-backend: ## Backend: lint, format check, type check, tests + coverage gate
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest --cov

check-frontend: require-node ## Frontend: lint, format check, type check, tests + coverage gate
	cd frontend && npm run check

require-node:
	@node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= $(NODE_MAJOR) ? 0 : 1)' || \
		{ echo "Node $(NODE_MAJOR)+ is required (found $$(node --version)). Run: nvm use $(NODE_MAJOR)"; exit 1; }
