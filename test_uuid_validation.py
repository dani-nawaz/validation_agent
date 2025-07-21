#!/usr/bin/env python3
"""
Comprehensive UUID validation tests for the Student Validation API.

Tests various UUID scenarios:
1. Valid UUID (existing in database)
2. Valid UUID format (but non-existent in database)  
3. Invalid UUID format
4. Null/None UUID
5. Empty string UUID
6. Malformed UUID strings
"""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any
import requests
import time
from api.services import ValidationServiceFactory
from api.repositories import MongoEnrollmentRepository
from api.exceptions import InvalidUuidFormatError, EnrollmentNotFoundError, ValidationServiceError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UUIDTestCase:
    """Test case for UUID validation."""
    def __init__(self, name: str, uuid_value: Any, expected_result: str, description: str):
        self.name = name
        self.uuid_value = uuid_value
        self.expected_result = expected_result  # 'success', 'invalid_format', 'not_found', 'error'
        self.description = description


async def test_service_level_validation():
    """Test UUID validation at the service level."""
    print("🔍 Testing Service-Level UUID Validation...")
    print("=" * 50)
    
    try:
        service = ValidationServiceFactory.create_mongo_service()
        repo = MongoEnrollmentRepository()
        
        # Get a valid UUID from database for testing
        valid_uuids = repo.get_all_uuids()
        valid_uuid = valid_uuids[0] if valid_uuids else None
        
        test_cases = [
            UUIDTestCase(
                "Valid existing UUID",
                valid_uuid,
                "success",
                "UUID exists in database and should validate successfully"
            ),
            UUIDTestCase(
                "Valid format but non-existent UUID",
                "12345678-1234-5678-9012-123456789012", 
                "not_found",
                "Valid UUID format but doesn't exist in database"
            ),
            UUIDTestCase(
                "Invalid UUID format - missing hyphens",
                "12345678123456789012123456789012",
                "invalid_format", 
                "UUID without proper hyphen formatting"
            ),
            UUIDTestCase(
                "Invalid UUID format - wrong length",
                "12345678-1234-5678-9012",
                "invalid_format",
                "UUID with incorrect length"
            ),
            UUIDTestCase(
                "Invalid UUID format - non-hex characters",
                "12345678-1234-5678-9012-12345678901z",
                "invalid_format",
                "UUID with non-hexadecimal characters"
            ),
            UUIDTestCase(
                "Null UUID",
                None,
                "invalid_format",
                "None/null value instead of UUID string"
            ),
            UUIDTestCase(
                "Empty string UUID",
                "",
                "invalid_format",
                "Empty string instead of UUID"
            ),
            UUIDTestCase(
                "UUID with extra characters",
                "12345678-1234-5678-9012-123456789012-extra",
                "invalid_format",
                "UUID with additional characters"
            ),
            UUIDTestCase(
                "Uppercase UUID",
                "12345678-1234-5678-9012-123456789012".upper(),
                "not_found",
                "Valid UUID format in uppercase (should be case-insensitive)"
            ),
            UUIDTestCase(
                "Mixed case UUID",
                "12345678-1234-5678-9012-123456789ABC",
                "not_found",
                "Valid UUID format with mixed case"
            )
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case.name}")
            print(f"   UUID: {test_case.uuid_value}")
            print(f"   Description: {test_case.description}")
            
            try:
                if test_case.uuid_value is None:
                    # Handle None case specially
                    try:
                        await service.initiate_validation(test_case.uuid_value)
                        result = "unexpected_success"
                        print("   ❌ UNEXPECTED: Validation succeeded with None UUID")
                    except (TypeError, AttributeError):
                        result = "invalid_format"
                        print("   ✅ EXPECTED: Rejected None UUID")
                    except Exception as e:
                        result = "error"
                        print(f"   ⚠️  UNEXPECTED ERROR: {e}")
                else:
                    process = await service.initiate_validation(str(test_case.uuid_value))
                    result = "success"
                    print(f"   ✅ SUCCESS: Process created {process.process_id}")
                    
            except InvalidUuidFormatError:
                result = "invalid_format"
                print("   ✅ EXPECTED: Invalid UUID format rejected")
                
            except EnrollmentNotFoundError:
                result = "not_found"
                print("   ✅ EXPECTED: UUID not found in database")
                
            except ValidationServiceError as e:
                result = "error"
                print(f"   ⚠️  SERVICE ERROR: {e}")
                
            except Exception as e:
                result = "error"
                print(f"   ❌ UNEXPECTED ERROR: {e}")
            
            # Check if result matches expectation
            if result == test_case.expected_result:
                print(f"   ✅ RESULT: {result} (matches expected)")
                results.append((test_case.name, True, result))
            else:
                print(f"   ❌ RESULT: {result} (expected {test_case.expected_result})")
                results.append((test_case.name, False, result))
        
        return results
        
    except Exception as e:
        print(f"❌ Service validation test failed: {e}")
        return []


async def test_api_level_validation():
    """Test UUID validation at the API level using HTTP requests."""
    print("\n🔍 Testing API-Level UUID Validation...")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Check if API is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API health check failed - make sure the API is running")
            return []
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API - make sure it's running at http://localhost:8000")
        return []
    
    # Get a valid UUID from database
    try:
        repo = MongoEnrollmentRepository()
        valid_uuids = repo.get_all_uuids()
        valid_uuid = valid_uuids[0] if valid_uuids else "387ec43c-6280-11f0-9d8d-4b43610f4997"
    except Exception:
        valid_uuid = "387ec43c-6280-11f0-9d8d-4b43610f4997"  # fallback
    
    test_cases = [
        {
            "name": "Valid existing UUID",
            "payload": {"uuid_str": valid_uuid},
            "expected_status": 201,
            "description": "Should create validation process successfully"
        },
        {
            "name": "Valid format but non-existent UUID", 
            "payload": {"uuid_str": "12345678-1234-5678-9012-123456789012"},
            "expected_status": 404,
            "description": "Should return 404 Not Found"
        },
        {
            "name": "Invalid UUID format - no hyphens",
            "payload": {"uuid_str": "12345678123456789012123456789012"},
            "expected_status": 422,
            "description": "Should return 422 Validation Error"
        },
        {
            "name": "Invalid UUID format - wrong length",
            "payload": {"uuid_str": "12345678-1234-5678"},
            "expected_status": 422,
            "description": "Should return 422 Validation Error"
        },
        {
            "name": "Empty string UUID",
            "payload": {"uuid_str": ""},
            "expected_status": 422,
            "description": "Should return 422 Validation Error"
        },
        {
            "name": "Missing uuid_str field",
            "payload": {},
            "expected_status": 422,
            "description": "Should return 422 Validation Error"
        },
        {
            "name": "Null uuid_str field",
            "payload": {"uuid_str": None},
            "expected_status": 422,
            "description": "Should return 422 Validation Error"
        },
        {
            "name": "Invalid JSON payload",
            "payload": "invalid json",
            "expected_status": 422,
            "description": "Should return 422 for malformed JSON"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Payload: {test_case['payload']}")
        
        try:
            if isinstance(test_case['payload'], str):
                # Test malformed JSON
                response = requests.post(
                    f"{base_url}/api/validate",
                    data=test_case['payload'],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            else:
                response = requests.post(
                    f"{base_url}/api/validate",
                    json=test_case['payload'],
                    timeout=10
                )
            
            actual_status = response.status_code
            expected_status = test_case['expected_status']
            
            print(f"   Status Code: {actual_status}")
            
            if actual_status == expected_status:
                print(f"   ✅ SUCCESS: Status {actual_status} matches expected")
                results.append((test_case['name'], True, actual_status))
                
                # Show response for successful validations
                if actual_status == 201:
                    response_data = response.json()
                    print(f"   Process ID: {response_data.get('process_id')}")
                    print(f"   Status: {response_data.get('status')}")
                
            else:
                print(f"   ❌ FAILURE: Status {actual_status} (expected {expected_status})")
                results.append((test_case['name'], False, actual_status))
            
            # Show error details for failures
            if actual_status >= 400:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'N/A')}")
                except:
                    print(f"   Raw response: {response.text[:100]}")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST ERROR: {e}")
            results.append((test_case['name'], False, "request_error"))
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {e}")
            results.append((test_case['name'], False, "unexpected_error"))
    
    return results


async def test_uuid_format_validation():
    """Test UUID format validation utility function."""
    print("\n🔍 Testing UUID Format Validation Function...")
    print("=" * 40)
    
    from api.services import EnrollmentValidationService
    
    # Create a service instance to test the validation method
    service = ValidationServiceFactory.create_mongo_service()
    
    test_cases = [
        ("Valid UUID lowercase", "12345678-1234-5678-9012-123456789abc", True),
        ("Valid UUID uppercase", "12345678-1234-5678-9012-123456789ABC", True),
        ("Valid UUID mixed case", "12345678-1234-5678-9012-123456789AbC", True),
        ("Invalid - no hyphens", "123456781234567890123456789abc", False),
        ("Invalid - wrong positions", "12345678_1234_5678_9012_123456789abc", False),
        ("Invalid - too short", "12345678-1234-5678-9012", False),
        ("Invalid - too long", "12345678-1234-5678-9012-123456789abc-extra", False),
        ("Invalid - non-hex chars", "12345678-1234-5678-9012-123456789xyz", False),
        ("Empty string", "", False),
        ("Only hyphens", "--------", False),
    ]
    
    results = []
    
    for name, test_uuid, expected in test_cases:
        try:
            result = service._validate_uuid_format(test_uuid)
            success = result == expected
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {name}: '{test_uuid}' -> {result} (expected {expected})")
            results.append((name, success, result))
        except Exception as e:
            print(f"❌ ERROR {name}: {e}")
            results.append((name, False, "error"))
    
    return results


async def main():
    """Main test function."""
    print("🚀 Comprehensive UUID Validation Test Suite")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        ("UUID Format Validation", test_uuid_format_validation),
        ("Service Level Validation", test_service_level_validation), 
        ("API Level Validation", test_api_level_validation),
    ]
    
    for suite_name, test_func in test_suites:
        try:
            print(f"\n📋 Running {suite_name}...")
            results = await test_func()
            all_results.extend([(suite_name, test_name, success, result) for test_name, success, result in results])
        except Exception as e:
            print(f"❌ {suite_name} failed with error: {e}")
            all_results.append((suite_name, "Test Suite", False, str(e)))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, _, success, _ in all_results if success)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
    
    print("\n📋 Detailed Results:")
    for suite_name, test_name, success, result in all_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} [{suite_name}] {test_name}: {result}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! UUID validation is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review the results above.")


if __name__ == "__main__":
    asyncio.run(main()) 