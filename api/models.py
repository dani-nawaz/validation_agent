from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class ValidationStatus(str, Enum):
    """Validation process status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidateStudentRequest(BaseModel):
    """Request model for student validation."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997"
            }
        }
    )
    
    uuid_str: str = Field(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="Enrollment UUID in standard UUID format"
    )


class ValidationProcessResponse(BaseModel):
    """Response model for validation process initiation."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "process_id": "550e8400-e29b-41d4-a716-446655440000",
                "uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997",
                "email": "alishba.tasleem+1@clickchain.com",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z",
                "message": "Validation process initiated successfully"
            }
        }
    )
    
    process_id: str = Field(..., description="Unique identifier for tracking the validation process")
    uuid_str: str = Field(..., description="Enrollment UUID being validated")
    email: Optional[str] = Field(None, description="Email associated with the enrollment")
    status: ValidationStatus = Field(..., description="Current status of the validation process")
    created_at: datetime = Field(..., description="Timestamp when the process was created")
    message: str = Field(..., description="Human-readable message about the process")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Invalid student ID format",
                "detail": "Student ID must follow format STU### (e.g., STU001)",
                "code": "INVALID_FORMAT"
            }
        }
    )
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error description")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")


class ValidationProcess(BaseModel):
    """Internal model representing a validation process."""
    process_id: str
    uuid_str: str
    email: Optional[str] = None
    status: ValidationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[dict] = None 