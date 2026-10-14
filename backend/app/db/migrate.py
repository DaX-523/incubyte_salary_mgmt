from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[2]


def alembic_config(database_url: str) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    # ConfigParser treats "%" as interpolation, e.g. in URL-encoded passwords.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    # Keep the host application's logging setup (e.g. uvicorn's) intact.
    config.attributes["configure_logger"] = False
    return config


def run_migrations(database_url: str) -> None:
    """Upgrade the database to the latest migration. Safe to call on every startup."""
    command.upgrade(alembic_config(database_url), "head")
