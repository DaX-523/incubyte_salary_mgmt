import pytest

from app.core.config import Settings, normalize_database_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql://u:p@db:5432/app", "postgresql+psycopg://u:p@db:5432/app"),
        ("postgres://u:p@db:5432/app", "postgresql+psycopg://u:p@db:5432/app"),
        ("postgresql+psycopg://u:p@db:5432/app", "postgresql+psycopg://u:p@db:5432/app"),
    ],
    ids=["postgresql-scheme", "postgres-alias", "already-psycopg"],
)
def test_normalize_database_url_selects_psycopg_driver(url: str, expected: str) -> None:
    assert normalize_database_url(url) == expected


def test_settings_read_database_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/salary")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://localhost/salary"


@pytest.mark.parametrize("value", [None, ""], ids=["missing", "empty"])
def test_settings_treat_blank_database_url_as_unset(value: str | None) -> None:
    assert Settings(_env_file=None, database_url=value).database_url is None
