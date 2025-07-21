# Student Validation API

A RESTful API built with FastAPI for initiating and tracking student validation processes. This API provides endpoints to validate student records with proper error handling, asynchronous processing, and MongoDB integration.

## Features

- **REST API**: Clean RESTful endpoints for validation operations
- **MongoDB Integration**: Production-ready MongoDB data storage
- **Async Processing**: Background validation processing with status tracking
- **SOLID Principles**: Clean architecture with dependency injection and separation of concerns
- **Comprehensive Error Handling**: Proper HTTP status codes and error responses
- **API Documentation**: Auto-generated Swagger UI and ReDoc documentation
- **Type Safety**: Full Pydantic model validation and type hints
- **Repository Pattern**: Abstracted data access layer for MongoDB
- **UUID Validation**: Comprehensive UUID format and existence validation

## Architecture

The API follows clean architecture principles with clear separation of concerns:

```
api/
├── __init__.py           # Package initialization
├── main.py              # FastAPI application and routes
├── models.py            # Pydantic models for request/response validation
├── services.py          # Business logic and validation services
├── repositories.py      # Data access layer abstractions
├── database.py          # MongoDB connection management
└── exceptions.py        # Custom exception classes
```

### Design Patterns Used

- **Repository Pattern**: Abstract data access
- **Dependency Injection**: Service composition
- **Factory Pattern**: Service creation
- **Strategy Pattern**: Validation strategies
- **Exception Handling**: Custom exceptions with proper HTTP mappings

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python start_api.py
```

Or directly with uvicorn:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### POST /api/validate

Initiate a validation process for a student.

**Request Body:**
```json
{
  "uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997"
}
```

**Response (201 Created):**
```json
{
  "process_id": "550e8400-e29b-41d4-a716-446655440000",
  "uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z",
  "message": "Validation process initiated successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid UUID format
- `404 Not Found`: Enrollment not found
- `500 Internal Server Error`: Service error

### GET /api/validate/{process_id}

Get the status of a validation process.

**Response (200 OK):**
```json
{
  "process_id": "550e8400-e29b-41d4-a716-446655440000",
  "uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00Z",
  "message": "Validation process completed successfully"
}
```

**Status Values:**
- `pending`: Process created but not started
- `in_progress`: Validation currently running
- `completed`: Validation finished successfully
- `failed`: Validation encountered an error

## Usage Examples

### cURL Examples

**Initiate Validation:**
```bash
curl -X POST "http://localhost:8000/api/validate" \
     -H "Content-Type: application/json" \
     -d '{"uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997"}'
```

**Check Status:**
```bash
curl -X GET "http://localhost:8000/api/validate/550e8400-e29b-41d4-a716-446655440000"
```

### Python Examples

```python
import requests
import time

# Initiate validation
response = requests.post(
    "http://localhost:8000/api/validate",
    json={"uuid_str": "387ec43c-6280-11f0-9d8d-4b43610f4997"}
)

if response.status_code == 201:
    data = response.json()
    process_id = data["process_id"]
    print(f"Validation started: {process_id}")
    
    # Poll for completion
    while True:
        status_response = requests.get(
            f"http://localhost:8000/api/validate/{process_id}"
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Status: {status_data['status']}")
            
            if status_data["status"] in ["completed", "failed"]:
                break
                
        time.sleep(1)
else:
    print(f"Error: {response.json()}")
```

### JavaScript/Node.js Examples

```javascript
const axios = require('axios');

async function validateEnrollment(uuidStr) {
    try {
        // Initiate validation
        const response = await axios.post('http://localhost:8000/api/validate', {
            uuid_str: uuidStr
        });
        
        const { process_id } = response.data;
        console.log(`Validation started: ${process_id}`);
        
        // Poll for completion
        while (true) {
            const statusResponse = await axios.get(
                `http://localhost:8000/api/validate/${process_id}`
            );
            
            const { status } = statusResponse.data;
            console.log(`Status: ${status}`);
            
            if (status === 'completed' || status === 'failed') {
                break;
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

validateEnrollment('387ec43c-6280-11f0-9d8d-4b43610f4997');
```

## Configuration

### Environment Variables

- `MONGODB_URI`: MongoDB connection string (required for production)
- `DB_NAME`: Database name (default: "lifetechacademy")
- `OPENAI_API_KEY`: Required for advanced document validation features
- `LOG_LEVEL`: Logging level (default: "INFO")

### Student Data Format

**MongoDB Collections:**
- `enrollmentForm`: Primary student enrollment data
- `students`: Secondary student data (fallback)

**Expected fields:**
- `uuid_str`: Enrollment UUID (primary identifier)
- `email`: Contact email
- `phone`: Contact phone number
- `students_info`: Array of student information objects containing:
  - `first_name`, `last_name`: Student names
  - `birthdate`: Date of birth
  - `address`: Address information
  - `documents`: Uploaded documents (birth certificates, etc.)
  - `medical_info`: Medical information
  - `care_giver_info`: Guardian/parent information
- `verification`: Verification status and timestamps

**Production Note:**
The API is designed for production use with MongoDB only. No CSV fallback is available.

## Development

### Adding New Validation Types

1. Extend the `ValidationService` interface in `services.py`
2. Implement new validation logic
3. Add corresponding models in `models.py`
4. Update API endpoints as needed

### Testing

```bash
# Test MongoDB integration
python test_api.py

# Test UUID validation scenarios
python test_uuid_validation.py

# Test database connection only
python api/database.py

# Install test dependencies (for future unit tests)
pip install pytest pytest-asyncio httpx

# Run tests (when test files are created)
pytest tests/
```

### Code Style

The project follows Python best practices:
- Type hints throughout
- Pydantic models for validation
- Async/await for I/O operations
- Proper exception handling
- Clean code principles

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup

```bash
# Production environment variables
export OPENAI_API_KEY=your_openai_api_key_here
export LOG_LEVEL=INFO
export WORKERS=4

# Run with Gunicorn for production
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Specification

The API follows OpenAPI 3.0 specification. Full specification is available at:
- http://localhost:8000/openapi.json

## Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review error messages and status codes
3. Ensure student data is properly formatted
4. Verify all dependencies are installed

## License


This project is part of the Student Validation System. 