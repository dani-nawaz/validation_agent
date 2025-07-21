"""
UUID validation tests using pytest.
"""

import pytest
from api.services import ValidationServiceFactory
from api.exceptions import InvalidUuidFormatError, EnrollmentNotFoundError, ValidationServiceError


@pytest.mark.unit
class TestUUIDFormatValidation:
    """Test UUID format validation."""

    @pytest.fixture
    def validation_service(self):
        """Get validation service for testing."""
        return ValidationServiceFactory.create_mongo_service()

    @pytest.mark.parametrize("uuid_str,expected", [
        ("12345678-1234-5678-9012-123456789abc", True),
        ("12345678-1234-5678-9012-123456789ABC", True),
        ("12345678-1234-5678-9012-123456789AbC", True),
        ("123456781234567890123456789abc", False),
        ("12345678_1234_5678_9012_123456789abc", False),
        ("12345678-1234-5678-9012", False),
        ("12345678-1234-5678-9012-123456789abc-extra", False),
        ("12345678-1234-5678-9012-123456789xyz", False),
        ("", False),
        ("--------", False),
    ])
    def test_uuid_format_validation(self, validation_service, uuid_str, expected):
        """Test UUID format validation with various inputs."""
        result = validation_service._validate_uuid_format(uuid_str)
        assert result == expected

    def test_none_uuid_handling(self, validation_service):
        """Test handling of None UUID."""
        with pytest.raises((TypeError, AttributeError)):
            validation_service._validate_uuid_format(None)


@pytest.mark.integration 
class TestServiceLevelValidation:
    """Test validation at the service level."""

    @pytest.mark.asyncio
    async def test_valid_existing_uuid(self, validation_service, valid_enrollment_uuid):
        """Test validation with valid existing UUID."""
        process = await validation_service.initiate_validation(valid_enrollment_uuid)
        
        assert process is not None
        assert process.process_id is not None
        assert process.uuid_str == valid_enrollment_uuid
        assert process.status is not None

    @pytest.mark.asyncio
    async def test_valid_format_nonexistent_uuid(self, validation_service):
        """Test validation with valid format but non-existent UUID."""
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        with pytest.raises(EnrollmentNotFoundError):
            await validation_service.initiate_validation(fake_uuid)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_uuid", [
        "12345678123456789012123456789012",  # no hyphens
        "12345678-1234-5678-9012",  # too short
        "12345678-1234-5678-9012-12345678901z",  # non-hex chars
        "",  # empty string
        "12345678-1234-5678-9012-123456789012-extra",  # extra chars
    ])
    async def test_invalid_uuid_format(self, validation_service, invalid_uuid):
        """Test validation with invalid UUID formats."""
        with pytest.raises(InvalidUuidFormatError):
            await validation_service.initiate_validation(invalid_uuid)

    @pytest.mark.asyncio
    async def test_none_uuid(self, validation_service):
        """Test validation with None UUID."""
        with pytest.raises((TypeError, AttributeError, InvalidUuidFormatError)):
            await validation_service.initiate_validation(None)

    @pytest.mark.asyncio
    async def test_case_insensitive_validation(self, validation_service):
        """Test that UUID validation is case-insensitive for valid formats."""
        test_uuid = "12345678-1234-5678-9012-123456789ABC"
        
        # Should not raise InvalidUuidFormatError (though may raise EnrollmentNotFoundError)
        with pytest.raises(EnrollmentNotFoundError):
            await validation_service.initiate_validation(test_uuid)

    @pytest.mark.asyncio
    async def test_validation_status_retrieval(self, validation_service, valid_enrollment_uuid):
        """Test retrieving validation status after initiation."""
        process = await validation_service.initiate_validation(valid_enrollment_uuid)
        
        # Retrieve status
        retrieved_process = await validation_service.get_validation_status(process.process_id)
        
        assert retrieved_process is not None
        assert retrieved_process.process_id == process.process_id
        assert retrieved_process.uuid_str == valid_enrollment_uuid


@pytest.mark.api
@pytest.mark.slow
class TestAPILevelValidation:
    """Test validation through the API endpoints."""

    @pytest.fixture
    def api_client(self):
        """HTTP client for API testing."""
        import httpx
        return httpx.Client(base_url="http://localhost:8000", timeout=10.0)

    def test_api_health_check(self, api_client):
        """Test that API is running."""
        try:
            response = api_client.get("/health")
            if response.status_code != 200:
                pytest.skip("API not available - start the API server")
        except Exception:
            pytest.skip("API not available - start the API server at http://localhost:8000")

    @pytest.mark.parametrize("payload,expected_status", [
        ({"uuid_str": "12345678-1234-5678-9012-123456789012"}, 404),  # valid format, not found
        ({"uuid_str": "12345678123456789012123456789012"}, 422),  # invalid format
        ({"uuid_str": "12345678-1234-5678"}, 422),  # invalid format
        ({"uuid_str": ""}, 422),  # empty string
        ({}, 422),  # missing field
        ({"uuid_str": None}, 422),  # null value
    ])
    def test_validation_endpoint_error_cases(self, api_client, payload, expected_status):
        """Test validation endpoint with various error cases."""
        self.test_api_health_check(api_client)
        
        response = api_client.post("/api/validate", json=payload)
        assert response.status_code == expected_status

    def test_validation_endpoint_success(self, api_client, valid_enrollment_uuid):
        """Test validation endpoint with valid UUID."""
        self.test_api_health_check(api_client)

        payload = {"uuid_str": valid_enrollment_uuid}
        response = api_client.post("/api/validate", json=payload)

        assert response.status_code in (200, 201)
        data = response.json()
        assert "process_id" in data
        assert "status" in data
        assert data["uuid_str"] == valid_enrollment_uuid

    def test_malformed_json(self, api_client):
        """Test API with malformed JSON."""
        self.test_api_health_check(api_client)
        
        response = api_client.post(
            "/api/validate",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422 