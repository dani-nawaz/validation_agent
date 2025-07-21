from typing import Optional


class ValidationAPIException(Exception):
    """Base exception for validation API errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class EnrollmentNotFoundError(ValidationAPIException):
    """Raised when an enrollment UUID is not found in the database."""
    
    def __init__(self, uuid_str: str):
        super().__init__(
            message=f"Enrollment UUID {uuid_str} not found",
            error_code="ENROLLMENT_NOT_FOUND",
            status_code=404
        )


class InvalidUuidFormatError(ValidationAPIException):
    """Raised when UUID format is invalid."""
    
    def __init__(self, uuid_str: str):
        super().__init__(
            message=f"Invalid UUID format: {uuid_str}. Expected standard UUID format",
            error_code="INVALID_UUID_FORMAT",
            status_code=400
        )


class ValidationProcessNotFoundError(ValidationAPIException):
    """Raised when a validation process is not found."""
    
    def __init__(self, process_id: str):
        super().__init__(
            message=f"Validation process {process_id} not found",
            error_code="PROCESS_NOT_FOUND",
            status_code=404
        )


class ValidationServiceError(ValidationAPIException):
    """Raised when validation service encounters an error."""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Validation service error: {message}",
            error_code="SERVICE_ERROR",
            status_code=500
        ) 