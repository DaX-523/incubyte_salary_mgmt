from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import APIRouter, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import employees, filters, health, insights, payrolls
from app.api.errors import register_error_handlers
from app.core.config import Settings, get_settings
from app.db.migrate import run_migrations

API_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    migrate: Callable[[str], None] = run_migrations,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database_url = resolved_settings.database_url
        if not database_url:
            yield
            return
        await to_thread.run_sync(migrate, database_url)
        engine = create_engine(database_url, pool_pre_ping=True)
        app.state.session_factory = sessionmaker(engine)
        try:
            yield
        finally:
            app.state.session_factory = None
            engine.dispose()

    app = FastAPI(title="Salary Management API", lifespan=lifespan)
    app.state.session_factory = None
    register_error_handlers(app)

    api = APIRouter(prefix=API_PREFIX)
    for module in (employees, payrolls, insights, filters):
        api.include_router(module.router)
    app.include_router(api)
    app.include_router(health.router)
    return app


app = create_app()
