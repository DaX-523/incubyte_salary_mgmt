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


class AuthenticationError(DomainError):
    """The caller could not be identified; the API answers 401."""


class InvalidCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        # The same message for an unknown email and a wrong password, so it reveals neither.
        super().__init__("Email or password is incorrect")


class NotAuthenticatedError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Log in to continue")


class SessionEndedError(AuthenticationError):
    """The token is invalid, expired, or from before the user last logged out."""

    def __init__(self) -> None:
        super().__init__("Your session has ended; log in again")
