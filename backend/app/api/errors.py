from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.dependencies import DatabaseNotConfiguredError
from app.domain.errors import ConflictError, DomainError, NotFoundError

ErrorHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
}


def register_error_handlers(app: FastAPI) -> None:
    for error_type, status_code in STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _respond_with(status_code))
    app.add_exception_handler(DatabaseNotConfiguredError, _database_not_configured)


def _respond_with(status_code: int) -> ErrorHandler:
    async def respond(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    return respond


async def _database_not_configured(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The database is not configured; set DATABASE_URL"},
    )
