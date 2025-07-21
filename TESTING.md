# Testing Guide

This project uses **pytest** as the testing framework, replacing the previous custom test runner.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python run_tests.py

# Or use pytest directly
pytest tests/
```

## Test Organization

```
tests/
├── __init__.py              # Test package
├── conftest.py             # Pytest fixtures and configuration
├── test_database.py        # Database connection and repository tests
├── test_uuid_validation.py # UUID validation tests  
└── test_validation_service.py # Service layer tests
```

## Test Categories

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests requiring database
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Tests that take more than a few seconds

## Running Specific Test Types

```bash
# Run only unit tests (fast)
python test_commands.py unit

# Run only integration tests
python test_commands.py integration

# Run only API tests (requires API server running)
python test_commands.py api

# Run fast tests (exclude slow ones)
python test_commands.py fast

# Run with coverage report
python test_commands.py coverage

# Run with verbose output
python test_commands.py verbose
```

## Prerequisites

### Database Tests
- MongoDB connection required
- Set `MONGODB_URI` environment variable (optional, uses default if not set)
- Database should contain enrollment documents for integration tests

### API Tests
- Requires API server running at `http://localhost:8000`
- Start the API with: `python start_api.py`

## Test Configuration

Configuration is in `pytest.ini`:
- Test discovery patterns
- Default options
- Marker definitions
- Asyncio support

## Fixtures

Common fixtures are defined in `tests/conftest.py`:
- `test_database` - Database connection
- `enrollment_repository` - Repository instance
- `validation_service` - Service instance
- `valid_enrollment_uuid` - Valid UUID from database
- `sample_enrollment_data` - Sample enrollment data

## Coverage Reports

```bash
# Generate coverage report
python test_commands.py coverage

# View HTML report
open htmlcov/index.html
```

## Best Practices

1. **Use appropriate markers** for test categorization
2. **Use fixtures** for common setup/teardown
3. **Parametrize tests** for multiple scenarios
4. **Skip tests** when prerequisites aren't met
5. **Use descriptive test names** that explain what's being tested

## Migration from Old Tests

The previous custom test files have been replaced:
- `test_api.py` → `tests/test_database.py` + `tests/test_validation_service.py`
- `test_uuid_validation.py` → `tests/test_uuid_validation.py`
- `run_tests.py` → Now uses pytest instead of custom runner

## Debugging Tests

```bash
# Run with detailed output
pytest -v -s tests/

# Run specific test
pytest tests/test_database.py::TestDatabaseConnection::test_mongodb_connection

# Run with pdb on failure
pytest --pdb tests/

# Stop on first failure
pytest -x tests/
``` 