import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/employees?month=2026-10",
        "/api/v1/employees/1",
        "/api/v1/payrolls/1",
        "/api/v1/insights/payroll-status?month=2026-10",
    ],
)
def test_data_endpoints_report_a_missing_database(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "The database is not configured; set DATABASE_URL"}
