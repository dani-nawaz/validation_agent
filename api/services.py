from abc import ABC, abstractmethod
from typing import Optional
import asyncio
from datetime import datetime, timezone

from api.models import ValidationProcess, ValidationStatus
from api.repositories import EnrollmentRepository, ValidationProcessRepository
from api.exceptions import (
    EnrollmentNotFoundError, 
    InvalidUuidFormatError,
    ValidationServiceError
)
import re


class ValidationService(ABC):
    """Abstract validation service interface."""
    
    @abstractmethod
    async def initiate_validation(self, uuid_str: str) -> ValidationProcess:
        """Initiate validation process for an enrollment."""
        pass
    
    @abstractmethod
    async def get_validation_status(self, process_id: str) -> Optional[ValidationProcess]:
        """Get status of a validation process."""
        pass


class EnrollmentValidationService(ValidationService):
    """Enrollment validation service implementation."""
    
    def __init__(
        self,
        enrollment_repository: EnrollmentRepository,
        process_repository: ValidationProcessRepository
    ):
        self.enrollment_repository = enrollment_repository
        self.process_repository = process_repository
    
    async def initiate_validation(self, uuid_str: str) -> ValidationProcess:
        """Initiate validation process for an enrollment."""
        # Validate UUID format
        if not self._validate_uuid_format(uuid_str):
            raise InvalidUuidFormatError(uuid_str)
        
        # Get enrollment data to extract email
        enrollment_data = self.enrollment_repository.get_by_uuid(uuid_str)
        if not enrollment_data:
            raise EnrollmentNotFoundError(uuid_str)
        
        try:
            # Extract email from enrollment data
            email = enrollment_data.get("email")
            
            # Create validation process with email
            process = self.process_repository.create(uuid_str, email)
            
            # Start async validation in background
            asyncio.create_task(self._perform_validation(process.process_id))
            
            return process
            
        except Exception as e:
            raise ValidationServiceError(f"Failed to initiate validation: {str(e)}")
    
    def _validate_uuid_format(self, uuid_str: str) -> bool:
        """Validate UUID format."""
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(uuid_pattern, uuid_str, re.IGNORECASE))
    
    async def get_validation_status(self, process_id: str) -> Optional[ValidationProcess]:
        """Get status of a validation process."""
        return self.process_repository.get_by_id(process_id)
    
    async def _perform_validation(self, process_id: str) -> None:
        """Perform the actual validation process in background."""
        try:
            # Update status to in_progress
            self.process_repository.update_status(
                process_id, 
                ValidationStatus.IN_PROGRESS
            )
            
            # Get the process details
            process = self.process_repository.get_by_id(process_id)
            if not process:
                return
            
            # Get enrollment data
            enrollment_data = self.enrollment_repository.get_by_uuid(process.uuid_str)
            if not enrollment_data:
                self.process_repository.update_status(
                    process_id,
                    ValidationStatus.FAILED,
                    error_message="Enrollment not found during validation"
                )
                return
            
            # Simulate validation process (in real implementation, this would call
            # the enhanced validation agent or document processing services)
            await asyncio.sleep(2)  # Simulate processing time
            
            # Extract student info for validation
            students_info = enrollment_data.get("students_info", [])
            
            # For now, mark as completed with enrollment data
            result_data = {
                "enrollment_validated": True,
                "enrollment_uuid": process.uuid_str,
                "email": enrollment_data.get("email"),
                "phone": enrollment_data.get("phone"),
                "students_count": len(students_info),
                "verification_status": enrollment_data.get("verification", {}).get("verified", False),
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "validation_notes": "Basic enrollment record validation completed"
            }
            
            self.process_repository.update_status(
                process_id,
                ValidationStatus.COMPLETED,
                result_data=result_data
            )
            
        except Exception as e:
            # Mark process as failed
            self.process_repository.update_status(
                process_id,
                ValidationStatus.FAILED,
                error_message=str(e)
            )


class ValidationServiceFactory:
    """Factory for creating validation service instances."""
    
    @staticmethod
    def create_default_service() -> ValidationService:
        """Create a default validation service with MongoDB storage."""
        return ValidationServiceFactory.create_mongo_service()
    
    @staticmethod
    def create_mongo_service() -> ValidationService:
        """Create a validation service with MongoDB storage."""
        from api.repositories import MongoEnrollmentRepository, MongoValidationProcessRepository
        
        enrollment_repo = MongoEnrollmentRepository()
        process_repo = MongoValidationProcessRepository()
        
        return EnrollmentValidationService(enrollment_repo, process_repo)
    
    @staticmethod
    def create_hybrid_service() -> ValidationService:
        """Create a validation service with MongoDB for enrollments and in-memory for processes."""
        from api.repositories import MongoEnrollmentRepository, InMemoryValidationProcessRepository
        
        enrollment_repo = MongoEnrollmentRepository()
        process_repo = InMemoryValidationProcessRepository()
        
        return EnrollmentValidationService(enrollment_repo, process_repo) 