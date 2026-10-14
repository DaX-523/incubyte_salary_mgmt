# Developer entry points for the monorepo. Run `make` to list targets.
.DEFAULT_GOAL := help
NODE_MAJOR := 24

.PHONY: help install dev-backend dev-frontend test format check check-backend check-frontend require-node

help: ## List available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-15s %s\n", $$1, $$2}'

install: require-node ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm install

dev-backend: ## Run the API with auto-reload on http://localhost:8000
	cd backend && uv run fastapi dev

dev-frontend: require-node ## Run the web app on http://localhost:3000
	cd frontend && npm run dev

test: require-node ## Run all unit tests (no coverage, fast feedback)
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
