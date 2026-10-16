import argparse
import string

import pytest

from app.core.config import Settings
from app.seed.__main__ import generate_demo_password, main, positive_int


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("10000", 10_000)])
def test_positive_int_accepts_positive_numbers(value: str, expected: int) -> None:
    assert positive_int(value) == expected


@pytest.mark.parametrize("value", ["0", "-5"])
def test_positive_int_rejects_zero_and_negatives(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="at least 1"):
        positive_int(value)


def test_cli_exits_with_usage_error_without_database_url(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([], settings=Settings(_env_file=None, database_url=None))

    assert exit_info.value.code == 2
    assert "DATABASE_URL is not set" in capsys.readouterr().err


def test_demo_passwords_are_random_url_safe_strings() -> None:
    password = generate_demo_password()

    assert len(password) == 16
    assert set(password) <= set(string.ascii_letters + string.digits + "-_")
