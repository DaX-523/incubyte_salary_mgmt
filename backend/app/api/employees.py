from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import EmployeeRepositoryDep, IdPath, PayrollRepositoryDep
from app.schemas.common import Page
from app.schemas.employees import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    MonthlyEmployee,
    MonthlyEmployeeFilters,
    MonthlyEmployeeQuery,
)
from app.schemas.payrolls import PayrollCreate, PayrollOut
from app.services import employee_export
from app.services import employees as employee_service
from app.services import payrolls as payroll_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("")
def list_employees_for_month(
    query: Annotated[MonthlyEmployeeQuery, Query()], employees: EmployeeRepositoryDep
) -> Page[MonthlyEmployee]:
    """Employees on the books in `month`, each with that month's payroll (null if unpaid)."""
    result = employee_service.list_employees_for_month(employees, query)
    return Page(
        items=[
            MonthlyEmployee(
                employee=EmployeeOut.from_model(employee),
                payroll=PayrollOut.from_model(payroll) if payroll else None,
            )
            for employee, payroll in result.rows
        ],
        total=result.total,
        page=query.page,
        page_size=query.page_size,
    )


# Declared before /{employee_id}, which would otherwise try to read "export" as an id.
@router.get(
    "/export",
    response_class=Response,
    responses={status.HTTP_200_OK: {"content": {"text/csv": {}}, "description": "CSV file"}},
)
def export_employees_for_month(
    filters: Annotated[MonthlyEmployeeFilters, Query()], employees: EmployeeRepositoryDep
) -> Response:
    """The monthly list as CSV: the same filters and order, every match on one sheet."""
    csv_text = employee_export.export_employees_for_month(employees, filters)
    return Response(content=csv_text, media_type="text/csv")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_employee(body: EmployeeCreate, employees: EmployeeRepositoryDep) -> EmployeeOut:
    return EmployeeOut.from_model(employee_service.create_employee(employees, body))


@router.get("/{employee_id}")
def get_employee(employee_id: IdPath, employees: EmployeeRepositoryDep) -> EmployeeOut:
    return EmployeeOut.from_model(employee_service.get_employee(employees, employee_id))


@router.patch("/{employee_id}")
def update_employee(
    employee_id: IdPath, body: EmployeeUpdate, employees: EmployeeRepositoryDep
) -> EmployeeOut:
    return EmployeeOut.from_model(employee_service.update_employee(employees, employee_id, body))


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_employee(employee_id: IdPath, employees: EmployeeRepositoryDep) -> None:
    """Marks the employee inactive. Nothing is deleted, so payroll history is kept."""
    employee_service.deactivate_employee(employees, employee_id)


@router.get("/{employee_id}/payrolls")
def list_employee_payrolls(
    employee_id: IdPath, employees: EmployeeRepositoryDep, payrolls: PayrollRepositoryDep
) -> list[PayrollOut]:
    """The employee's payrolls, newest month first. Not paginated: there is at most one a month."""
    return [
        PayrollOut.from_model(payroll)
        for payroll in payroll_service.list_employee_payrolls(employees, payrolls, employee_id)
    ]


@router.post("/{employee_id}/payrolls", status_code=status.HTTP_201_CREATED)
def create_payroll(
    employee_id: IdPath,
    body: PayrollCreate,
    employees: EmployeeRepositoryDep,
    payrolls: PayrollRepositoryDep,
) -> PayrollOut:
    """Records the employee's pay for a month, in their country's currency."""
    payroll = payroll_service.create_payroll(employees, payrolls, employee_id, body)
    return PayrollOut.from_model(payroll)
