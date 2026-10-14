"""Seed the database with demo data: `uv run python -m app.seed --help`."""

import argparse
import sys
from collections.abc import Sequence
from datetime import date

from sqlalchemy import create_engine

from app.core.config import Settings, get_settings
from app.db.migrate import run_migrations
from app.seed.generator import generate_seed_data, recent_months
from app.seed.writer import SeedAbortedError, seed_database

DEFAULT_EMPLOYEES = 10_000
DEFAULT_MONTHS = 12
DEFAULT_SEED = 42


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
    return parser


def main(
    argv: Sequence[str] | None = None,
    settings: Settings | None = None,
    today: date | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    database_url = (settings or get_settings()).database_url
    if not database_url:
        parser.error("DATABASE_URL is not set; add it to backend/.env or the environment")

    run_migrations(database_url)
    run_date = today or date.today()
    data = generate_seed_data(
        employee_count=args.employees,
        months=recent_months(run_date, args.months),
        today=run_date,
        seed=args.seed,
    )
    engine = create_engine(database_url)
    try:
        seed_database(engine, data, reset=args.reset)
    except SeedAbortedError as error:
        sys.stderr.write(f"Seed aborted: {error}\n")
        return 1
    finally:
        engine.dispose()

    sys.stdout.write(f"Seeded {len(data.employees)} employees and {len(data.payrolls)} payrolls.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
