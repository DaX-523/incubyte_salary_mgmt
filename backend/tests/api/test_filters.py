from fastapi import status
from fastapi.testclient import TestClient


def test_lists_the_allowed_filter_and_form_values(client: TestClient) -> None:
    response = client.get("/api/v1/filters")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["countries"][0] == {"code": "AU", "currency": "AUD"}
    assert body["job_titles"][0] == {"title": "Account Executive", "department": "Sales"}
    assert body["payment_methods"] == ["bank_transfer", "digital_wallet"]
