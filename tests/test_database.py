"""
Database connection and MongoDB integration tests.
"""

import pytest
from api.database import test_connection as db_test_connection, get_enrollment_collection
from api.repositories import MongoEnrollmentRepository


@pytest.mark.integration
def test_connection():
    """Test that the database connection works."""
    assert db_test_connection() is True


@pytest.mark.integration
class TestEnrollmentRepository:
    """Test enrollment repository functionality."""

    def test_repository_initialization(self, enrollment_repository):
        """Test that repository can be initialized."""
        assert enrollment_repository is not None
        assert isinstance(enrollment_repository, MongoEnrollmentRepository)

    def test_get_all_uuids(self, enrollment_repository):
        """Test getting all enrollment UUIDs."""
        uuids = enrollment_repository.get_all_uuids()
        assert isinstance(uuids, list)
        
        if uuids:
            # Check that UUIDs have correct format
            for uuid_str in uuids[:5]:  # Test first 5
                assert isinstance(uuid_str, str)
                assert len(uuid_str) == 36  # UUID length
                assert uuid_str.count('-') == 4  # UUID hyphens

    def test_get_by_uuid_existing(self, enrollment_repository, valid_enrollment_uuid):
        """Test retrieving existing enrollment by UUID."""
        enrollment = enrollment_repository.get_by_uuid(valid_enrollment_uuid)
        
        assert enrollment is not None
        assert isinstance(enrollment, dict)
        assert enrollment.get("uuid_str") == valid_enrollment_uuid

    def test_get_by_uuid_nonexistent(self, enrollment_repository):
        """Test retrieving non-existent enrollment by UUID."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        enrollment = enrollment_repository.get_by_uuid(fake_uuid)
        assert enrollment is None

    def test_exists_method(self, enrollment_repository, valid_enrollment_uuid):
        """Test the exists method."""
        # Test with existing UUID
        assert enrollment_repository.exists(valid_enrollment_uuid) is True
        
        # Test with non-existent UUID
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        assert enrollment_repository.exists(fake_uuid) is False

    def test_enrollment_data_structure(self, sample_enrollment_data):
        """Test the structure of enrollment data."""
        assert sample_enrollment_data is not None
        assert isinstance(sample_enrollment_data, dict)
        
        # Check for students_info
        if "students_info" in sample_enrollment_data:
            students_info = sample_enrollment_data["students_info"]
            assert isinstance(students_info, list)
            
            if students_info:
                first_student = students_info[0]
                assert isinstance(first_student, dict)
                # Add more specific assertions based on your student data structure 