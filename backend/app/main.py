from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import FastAPI

from app.api import health
from app.core.config import Settings, get_settings
from app.db.migrate import run_migrations


def create_app(
    settings: Settings | None = None,
    migrate: Callable[[str], None] = run_migrations,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if resolved_settings.database_url:
            await to_thread.run_sync(migrate, resolved_settings.database_url)
        yield

    app = FastAPI(title="Salary Management API", lifespan=lifespan)
    app.include_router(health.router)
    return app


app = create_app()
