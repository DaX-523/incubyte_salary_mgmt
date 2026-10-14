from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    # Explicit settings: unit tests never read backend/.env or touch a real database.
    return create_app(Settings(_env_file=None, database_url=None))


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
