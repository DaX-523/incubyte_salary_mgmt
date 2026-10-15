from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Path, Request
from sqlalchemy.orm import Session, sessionmaker

from app.repositories.employees import EmployeeRepository, SqlEmployeeRepository
from app.repositories.insights import InsightsRepository, SqlInsightsRepository
from app.repositories.payrolls import PayrollRepository, SqlPayrollRepository
from app.schemas.common import MAX_ID


class DatabaseNotConfiguredError(Exception):
    """The API was started without DATABASE_URL, so it cannot serve data."""


def get_session(request: Request) -> Iterator[Session]:
    session_factory: sessionmaker[Session] | None = request.app.state.session_factory
    if session_factory is None:
        raise DatabaseNotConfiguredError
    with session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_employee_repository(session: SessionDep) -> EmployeeRepository:
    return SqlEmployeeRepository(session)


def get_payroll_repository(session: SessionDep) -> PayrollRepository:
    return SqlPayrollRepository(session)


def get_insights_repository(session: SessionDep) -> InsightsRepository:
    return SqlInsightsRepository(session)


EmployeeRepositoryDep = Annotated[EmployeeRepository, Depends(get_employee_repository)]
PayrollRepositoryDep = Annotated[PayrollRepository, Depends(get_payroll_repository)]
InsightsRepositoryDep = Annotated[InsightsRepository, Depends(get_insights_repository)]
IdPath = Annotated[int, Path(ge=1, le=MAX_ID)]
