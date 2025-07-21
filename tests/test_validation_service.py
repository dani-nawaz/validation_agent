"""
Validation service tests.
"""

import pytest
import asyncio
from api.services import ValidationServiceFactory
from api.repositories import MongoEnrollmentRepository


@pytest.mark.integration
class TestValidationService:
    """Test validation service functionality."""

    @pytest.mark.asyncio
    async def test_service_creation(self, validation_service):
        """Test that validation service can be created."""
        assert validation_service is not None

    @pytest.mark.asyncio
    async def test_validation_process_creation(self, validation_service, valid_enrollment_uuid):
        """Test creating a validation process."""
        process = await validation_service.initiate_validation(valid_enrollment_uuid)
        
        assert process is not None
        assert process.process_id is not None
        assert process.uuid_str == valid_enrollment_uuid
        assert process.status is not None

    @pytest.mark.asyncio
    async def test_validation_status_retrieval(self, validation_service, valid_enrollment_uuid):
        """Test retrieving validation process status."""
        # Create a process
        process = await validation_service.initiate_validation(valid_enrollment_uuid)
        
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Retrieve status
        updated_process = await validation_service.get_validation_status(process.process_id)
        
        assert updated_process is not None
        assert updated_process.process_id == process.process_id
        assert updated_process.uuid_str == valid_enrollment_uuid

    @pytest.mark.asyncio
    async def test_nonexistent_process_status(self, validation_service):
        """Test retrieving status for non-existent process."""
        fake_process_id = "nonexistent-process-id"
        result = await validation_service.get_validation_status(fake_process_id)
        
        # Should return None or raise an appropriate exception
        assert result is None 