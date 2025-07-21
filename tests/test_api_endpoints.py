"""
API endpoint tests for the Student Validation API.
"""

import pytest
import httpx
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def is_api_server_running():
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=2.0) as client:
            resp = client.get("/health")
            return resp.status_code == 200
    except Exception:
        return False

@pytest.mark.api
@pytest.mark.slow
class TestAPIEndpoints:
    @pytest.fixture(scope="class", autouse=True)
    def _skip_if_server_not_running(self):
        if not is_api_server_running():
            pytest.skip(f"API server is not running at {API_BASE_URL}")

    @pytest.fixture(scope="class")
    def client(self):
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            yield client

    def test_health_check(self, client):
        """Test the /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        status = response.json().get("status", "").lower()
        assert status in ("ok", "healthy", "running"), f"Health status is '{status}', expected one of: ok, healthy, running. Full response: {response.json()}"

    def test_validation_endpoint_success(self, client, valid_enrollment_uuid):
        """Test /api/validate with a valid UUID."""
        payload = {"uuid_str": valid_enrollment_uuid}
        response = client.post("/api/validate", json=payload)
        assert response.status_code in (200, 201)
        data = response.json()
        assert "process_id" in data
        assert data["uuid_str"] == valid_enrollment_uuid
        assert data["status"]

    @pytest.mark.parametrize("payload,expected_status", [
        ({"uuid_str": "12345678-1234-5678-9012-123456789012"}, 404),  # valid format, not found
        ({"uuid_str": "12345678123456789012123456789012"}, 422),  # invalid format
        ({"uuid_str": "12345678-1234-5678"}, 422),  # invalid format
        ({"uuid_str": ""}, 422),  # empty string
        ({}, 422),  # missing field
        ({"uuid_str": None}, 422),  # null value
    ])
    def test_validation_endpoint_error_cases(self, client, payload, expected_status):
        """Test /api/validate with various error cases."""
        response = client.post("/api/validate", json=payload)
        assert response.status_code == expected_status

    def test_validation_endpoint_malformed_json(self, client):
        """Test /api/validate with malformed JSON."""
        response = client.post(
            "/api/validate",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422 