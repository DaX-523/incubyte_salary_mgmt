"""Seed the database with demo data: `uv run python -m app.seed --help`."""

import argparse
import secrets
import sys
from collections.abc import Callable, Sequence
from datetime import date

from sqlalchemy import create_engine

from app.core.config import Settings, get_settings
from app.db.migrate import run_migrations
from app.seed.generator import generate_seed_data, recent_months
from app.seed.writer import DEMO_LOGIN_EMAIL, SeedAbortedError, reset_demo_login, seed_database

DEFAULT_EMPLOYEES = 10_000
DEFAULT_MONTHS = 12
DEFAULT_SEED = 42
# Random bytes for the demo login's password, shown once and stored nowhere but as a hash.
DEMO_PASSWORD_BYTES = 12


def generate_demo_password() -> str:
    return secrets.token_urlsafe(DEMO_PASSWORD_BYTES)


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {number}")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Fill the database with deterministic demo employees and payroll history.",
    )
    parser.add_argument("--employees", type=positive_int, default=DEFAULT_EMPLOYEES)
    parser.add_argument(
        "--months", type=positive_int, default=DEFAULT_MONTHS, help="payroll history length"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="random seed")
    parser.add_argument(
        "--reset", action="store_true", help="delete existing employees and payrolls first"
    )
    parser.add_argument(
        "--demo-login-only",
        action="store_true",
        help="only create the demo login, or give it a new password; no other data changes",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    settings: Settings | None = None,
    today: date | None = None,
    new_password: Callable[[], str] = generate_demo_password,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    database_url = (settings or get_settings()).database_url
    if not database_url:
        parser.error("DATABASE_URL is not set; add it to backend/.env or the environment")

    run_migrations(database_url)
    password = new_password()
    engine = create_engine(database_url)
    try:
        if args.demo_login_only:
            reset_demo_login(engine, password)
        else:
            run_date = today or date.today()
            data = generate_seed_data(
                employee_count=args.employees,
                months=recent_months(run_date, args.months),
                today=run_date,
                seed=args.seed,
            )
            seed_database(engine, data, demo_password=password, reset=args.reset)
            sys.stdout.write(
                f"Seeded {len(data.employees)} employees and {len(data.payrolls)} payrolls.\n"
            )
    except SeedAbortedError as error:
        sys.stderr.write(f"Seed aborted: {error}\n")
        return 1
    finally:
        engine.dispose()

    sys.stdout.write(f"Demo login: {DEMO_LOGIN_EMAIL} / {password} (shown only this once)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
