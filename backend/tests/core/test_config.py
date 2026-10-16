import pytest
from pydantic import SecretStr

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


def test_settings_accept_a_jwt_secret_of_32_characters() -> None:
    settings = Settings(_env_file=None, jwt_secret=SecretStr("x" * 32))

    assert settings.jwt_secret is not None
    assert settings.jwt_secret.get_secret_value() == "x" * 32


def test_settings_reject_a_jwt_secret_shorter_than_32_characters() -> None:
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(_env_file=None, jwt_secret=SecretStr("x" * 31))


@pytest.mark.parametrize("value", [None, SecretStr("")], ids=["missing", "empty"])
def test_settings_treat_a_blank_jwt_secret_as_unset(value: SecretStr | None) -> None:
    assert Settings(_env_file=None, jwt_secret=value).jwt_secret is None


def test_settings_read_the_jwt_secret_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "y" * 32)

    settings = Settings(_env_file=None)

    assert settings.jwt_secret is not None
    assert settings.jwt_secret.get_secret_value() == "y" * 32


def test_settings_keep_the_jwt_secret_out_of_their_repr() -> None:
    settings = Settings(_env_file=None, jwt_secret=SecretStr("s" * 40))

    assert "s" * 40 not in repr(settings)
