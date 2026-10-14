from dataclasses import asdict

from sqlalchemy import Engine, func, insert, select, text
from sqlalchemy.orm import Session

from app.db.models import Employee, Payroll
from app.seed.generator import SeedData


class SeedAbortedError(Exception):
    """Raised instead of mixing demo data into a database that already has employees."""


def seed_database(engine: Engine, data: SeedData, *, reset: bool = False) -> None:
    """Insert `data` in a single transaction; with `reset`, replace existing rows first."""
    with Session(engine) as session, session.begin():
        existing = session.scalar(select(func.count()).select_from(Employee))
        if existing and not reset:
            raise SeedAbortedError(
                f"employees already has {existing} rows; re-run with --reset to replace them"
            )
        if reset:
            session.execute(text("TRUNCATE payrolls, employees RESTART IDENTITY"))

        employee_ids = session.scalars(
            insert(Employee).returning(Employee.id, sort_by_parameter_order=True),
            [asdict(employee) for employee in data.employees],
        ).all()
        if data.payrolls:
            session.execute(
                insert(Payroll),
                [
                    {
                        "employee_id": employee_ids[payroll.employee_index],
                        "month": payroll.month,
                        "base": payroll.base,
                        "bonus": payroll.bonus,
                        "esops": payroll.esops,
                        "currency": payroll.currency,
                        "payment_method": payroll.payment_method,
                        "created_at": payroll.paid_at,
                        "updated_at": payroll.paid_at,
                    }
                    for payroll in data.payrolls
                ],
            )
