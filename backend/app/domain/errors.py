"""Business rule violations. Services and repositories raise them; only the API layer maps them to
HTTP status codes."""

from datetime import date


class DomainError(Exception):
    """Base class: the message is safe to show to API clients."""


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class EmployeeNotFoundError(NotFoundError):
    def __init__(self, employee_id: int) -> None:
        super().__init__(f"Employee {employee_id} not found")


class PayrollNotFoundError(NotFoundError):
    def __init__(self, payroll_id: int) -> None:
        super().__init__(f"Payroll {payroll_id} not found")


class DuplicateEmailError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"An employee with email {email} already exists")


class DuplicatePayrollError(ConflictError):
    def __init__(self, employee_id: int, month: date) -> None:
        super().__init__(f"Employee {employee_id} already has a payroll for {month:%Y-%m}")


class InactiveEmployeeError(ConflictError):
    def __init__(self, employee_id: int) -> None:
        super().__init__(f"Employee {employee_id} is inactive, so no new payrolls can be added")
