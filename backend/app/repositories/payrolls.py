from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.domain.errors import DuplicatePayrollError
from app.repositories.errors import violates_unique_constraint


class PayrollRepository(Protocol):
    def get(self, payroll_id: int) -> Payroll | None: ...

    def list_for_employee(self, employee_id: int) -> list[Payroll]: ...

    def add(self, payroll: Payroll) -> Payroll: ...

    def save(self, payroll: Payroll) -> Payroll: ...


class SqlPayrollRepository:
    """Reads only the payrolls of one organization's employees. New payrolls are added for an
    employee already loaded through that organization's employee repository."""

    def __init__(self, session: Session, organization_id: int) -> None:
        self._session = session
        self._organization_id = organization_id

    def get(self, payroll_id: int) -> Payroll | None:
        return self._session.scalar(
            select(Payroll)
            .join(Employee, Employee.id == Payroll.employee_id)
            .where(Payroll.id == payroll_id, Employee.organization_id == self._organization_id)
        )

    def list_for_employee(self, employee_id: int) -> list[Payroll]:
        """Newest month first. Served by the (employee_id, month) unique index."""
        return list(
            self._session.scalars(
                select(Payroll)
                .join(Employee, Employee.id == Payroll.employee_id)
                .where(
                    Payroll.employee_id == employee_id,
                    Employee.organization_id == self._organization_id,
                )
                .order_by(Payroll.month.desc())
            )
        )

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
