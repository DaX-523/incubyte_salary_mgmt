from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError


def violates_unique_constraint(error: IntegrityError, constraint_name: str) -> bool:
    cause = error.orig
    return isinstance(cause, UniqueViolation) and cause.diag.constraint_name == constraint_name
