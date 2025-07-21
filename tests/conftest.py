"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from api.database import test_connection, get_enrollment_collection
from api.services import ValidationServiceFactory
from api.repositories import MongoEnrollmentRepository


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database():
    """Test database connection fixture."""
    success = test_connection()
    if not success:
        pytest.skip("Database connection failed")
    return success


@pytest.fixture(scope="session")
def enrollment_collection(test_database):
    """Get enrollment collection fixture."""
    return get_enrollment_collection()


@pytest.fixture(scope="session")
def enrollment_repository(test_database):
    """Get enrollment repository fixture."""
    return MongoEnrollmentRepository()


@pytest.fixture(scope="session")
def validation_service(test_database):
    """Get validation service fixture."""
    return ValidationServiceFactory.create_mongo_service()


@pytest.fixture(scope="session")
def valid_enrollment_uuid(enrollment_repository) -> str:
    """Get a valid enrollment UUID from the database."""
    uuids = enrollment_repository.get_all_uuids()
    if not uuids:
        pytest.skip("No enrollment UUIDs found in database")
    return uuids[0]


@pytest.fixture(scope="session")
def sample_enrollment_data(enrollment_repository, valid_enrollment_uuid):
    """Get sample enrollment data."""
    return enrollment_repository.get_by_uuid(valid_enrollment_uuid) 