from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional
from datetime import datetime, timezone

from api.models import (
    ValidateStudentRequest, 
    ValidationProcessResponse, 
    ErrorResponse,
    ValidationStatus
)
from api.services import ValidationServiceFactory, ValidationService
from api.exceptions import ValidationAPIException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance
validation_service: Optional[ValidationService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application."""
    global validation_service
    
    # Startup
    logger.info("Starting Student Validation API...")
    
    try:
        logger.info("Initializing with MongoDB backend...")
        validation_service = ValidationServiceFactory.create_mongo_service()
        logger.info("MongoDB validation service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB backend: {e}")
        logger.info("Falling back to hybrid service (MongoDB for enrollments, in-memory for processes)...")
        try:
            validation_service = ValidationServiceFactory.create_hybrid_service()
            logger.info("Hybrid validation service initialized successfully")
        except Exception as fallback_error:
            logger.error(f"All backends failed: {fallback_error}")
            raise RuntimeError("Unable to initialize any validation service backend")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Student Validation API...")
    try:
        from api.database import DatabaseConnection
        DatabaseConnection.get_instance().close_connection()
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


# Create FastAPI application
app = FastAPI(
    title="Student Validation API",
    description="API for initiating and tracking student validation processes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationAPIException)
async def validation_exception_handler(request: Request, exc: ValidationAPIException):
    """Handle custom validation API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "code": exc.error_code,
            "detail": None
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid input",
            "detail": str(exc),
            "code": "INVALID_INPUT"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "message": "Student Validation API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "student-validation-api",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "unknown",
        "validation_service": "unknown"
    }
    
    # Check database connectivity
    try:
        from api.database import DatabaseConnection
        db = DatabaseConnection.get_instance()
        if db.is_connected():
            health_status["database"] = "connected"
        else:
            health_status["database"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check validation service
    if validation_service:
        health_status["validation_service"] = "initialized"
    else:
        health_status["validation_service"] = "not_initialized"
        health_status["status"] = "unhealthy"
    
    return health_status


@app.post(
    "/api/validate",
    response_model=ValidationProcessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid UUID format"},
        404: {"model": ErrorResponse, "description": "Enrollment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Validation"],
    summary="Initiate enrollment validation process",
    description="""
    Initiate a validation process for an enrollment by providing the enrollment UUID.
    
    The endpoint will:
    1. Validate the UUID format
    2. Check if the enrollment exists in the database
    3. Create a new validation process
    4. Start the validation in the background
    5. Return a process ID for tracking
    
    The validation process will run asynchronously and can be tracked using the returned process ID.
    """
)
async def validate_enrollment(request: ValidateStudentRequest) -> ValidationProcessResponse:
    """
    Initiate validation process for an enrollment.
    
    Args:
        request: Request containing enrollment UUID
        
    Returns:
        ValidationProcessResponse: Process ID and initial status
        
    Raises:
        HTTPException: If UUID is invalid or enrollment not found
    """
    if not validation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Validation service not available"
        )
    
    try:
        # Initiate validation process
        process = await validation_service.initiate_validation(request.uuid_str)
        
        # Return response
        return ValidationProcessResponse(
            process_id=process.process_id,
            uuid_str=process.uuid_str,
            email=process.email,
            status=process.status,
            created_at=process.created_at,
            message="Validation process initiated successfully"
        )
        
    except ValidationAPIException:
        # Re-raise custom exceptions to be handled by exception handler
        raise
    except Exception as e:
        logger.error(f"Unexpected error in validate_student: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate validation process"
        )


@app.get(
    "/api/validate/{process_id}",
    response_model=ValidationProcessResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Process not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Validation"],
    summary="Get validation process status",
    description="""
    Get the current status of a validation process by its ID.
    
    The response will include:
    - Current status (pending, in_progress, completed, failed)
    - Creation timestamp
    - Update timestamp (if available)
    - Result data (if completed)
    - Error message (if failed)
    """
)
async def get_validation_status(process_id: str) -> ValidationProcessResponse:
    """
    Get status of a validation process.
    
    Args:
        process_id: Unique identifier of the validation process
        
    Returns:
        ValidationProcessResponse: Current status and details
        
    Raises:
        HTTPException: If process not found
    """
    if not validation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Validation service not available"
        )
    
    try:
        process = await validation_service.get_validation_status(process_id)
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation process {process_id} not found"
            )
        
        # Determine message based on status
        status_messages = {
            ValidationStatus.PENDING: "Validation process is pending",
            ValidationStatus.IN_PROGRESS: "Validation process is in progress",
            ValidationStatus.COMPLETED: "Validation process completed successfully",
            ValidationStatus.FAILED: f"Validation process failed: {process.error_message or 'Unknown error'}"
        }
        
        return ValidationProcessResponse(
            process_id=process.process_id,
            uuid_str=process.uuid_str,
            email=process.email,
            status=process.status,
            created_at=process.created_at,
            message=status_messages.get(process.status, "Unknown status")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_validation_status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get validation status"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    ) 