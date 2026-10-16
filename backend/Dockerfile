# The API image that Fly.io deploys (see fly.toml). Build from backend/: docker build -t salary-api .
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Compile bytecode at build time so the first requests aren't slower, and copy packages out of the
# build cache instead of linking to it.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Dependencies first: they change less often than the code, so this layer is usually reused.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . .

RUN useradd --create-home api
USER api

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# DATABASE_URL and JWT_SECRET come from the environment; pending migrations run on startup.
CMD ["fastapi", "run", "--port", "8000"]
