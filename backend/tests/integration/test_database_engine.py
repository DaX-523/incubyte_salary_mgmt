from collections.abc import Iterator

import psycopg
import pytest
from sqlalchemy import Engine, text

from app.db.engine import create_database_engine

# Long enough for the terminated server process to exit, so the test never races it.
TERMINATION_WAIT_MS = 5_000
SELECT_BACKEND_PID = text("SELECT pg_backend_pid()")


@pytest.fixture
def api_engine(database_url: str) -> Iterator[Engine]:
    engine = create_database_engine(database_url)
    yield engine
    engine.dispose()


def test_reuses_a_connection_across_sessions(api_engine: Engine) -> None:
    with api_engine.connect() as connection:
        first_pid = connection.scalar(SELECT_BACKEND_PID)

    with api_engine.connect() as connection:
        second_pid = connection.scalar(SELECT_BACKEND_PID)

    assert second_pid == first_pid


def test_replaces_a_pooled_connection_the_database_closed(
    api_engine: Engine, migrated_engine: Engine
) -> None:
    with api_engine.connect() as connection:
        closed_pid = connection.scalar(SELECT_BACKEND_PID)
    with migrated_engine.connect() as admin:
        admin.execute(
            text("SELECT pg_terminate_backend(:pid, :wait_ms)"),
            {"pid": closed_pid, "wait_ms": TERMINATION_WAIT_MS},
        )

    with api_engine.connect() as connection:
        new_pid = connection.scalar(SELECT_BACKEND_PID)

    assert new_pid != closed_pid


def test_gives_up_on_a_silent_connection_after_three_seconds(api_engine: Engine) -> None:
    with api_engine.connect() as connection:
        driver_connection = connection.connection.driver_connection
        assert isinstance(driver_connection, psycopg.Connection)

        parameters = driver_connection.info.get_parameters()

    assert parameters["tcp_user_timeout"] == "3000"
