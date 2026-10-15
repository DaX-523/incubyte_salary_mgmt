from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Payroll
from app.domain.errors import DuplicatePayrollError
from app.repositories.errors import violates_unique_constraint


class PayrollRepository(Protocol):
    def get(self, payroll_id: int) -> Payroll | None: ...

    def add(self, payroll: Payroll) -> Payroll: ...

    def save(self, payroll: Payroll) -> Payroll: ...


class SqlPayrollRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, payroll_id: int) -> Payroll | None:
        return self._session.get(Payroll, payroll_id)

    def add(self, payroll: Payroll) -> Payroll:
        self._session.add(payroll)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if violates_unique_constraint(error, "uq_payrolls_employee_id_month"):
                raise DuplicatePayrollError(payroll.employee_id, payroll.month) from error
            raise
        self._session.refresh(payroll)
        return payroll

    def save(self, payroll: Payroll) -> Payroll:
        self._session.commit()
        self._session.refresh(payroll)
        return payroll
