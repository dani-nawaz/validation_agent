#!/usr/bin/env python3
"""
Test script for Student Validation API with MongoDB integration.
"""

import asyncio
import json
from api.database import test_connection, get_enrollment_collection
from api.services import ValidationServiceFactory
from api.repositories import MongoEnrollmentRepository
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test MongoDB database connection."""
    print("🔍 Testing MongoDB Connection...")
    print("=" * 40)
    
    try:
        success = test_connection()
        if success:
            print("✅ Database connection test passed")
            return True
        else:
            print("❌ Database connection test failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


async def test_enrollment_repository():
    """Test MongoDB enrollment repository."""
    print("\n🔍 Testing Enrollment Repository...")
    print("=" * 40)
    
    try:
        repo = MongoEnrollmentRepository()
        
        # Test get_all_uuids
        enrollment_uuids = repo.get_all_uuids()
        print(f"✅ Found {len(enrollment_uuids)} enrollment UUIDs")
        
        if enrollment_uuids:
            # Test get_by_uuid with first enrollment
            first_uuid = enrollment_uuids[0]
            enrollment = repo.get_by_uuid(first_uuid)
            
            if enrollment:
                print(f"✅ Successfully retrieved enrollment: {first_uuid}")
                print(f"   Enrollment data keys: {list(enrollment.keys())}")
                
                # Check students_info
                students_info = enrollment.get("students_info", [])
                print(f"   Students in enrollment: {len(students_info)}")
                
                if students_info:
                    first_student = students_info[0]
                    print(f"   First student name: {first_student.get('first_name')} {first_student.get('last_name')}")
            else:
                print(f"❌ Failed to retrieve enrollment: {first_uuid}")
                return False
            
            # Test exists
            exists = repo.exists(first_uuid)
            print(f"✅ Enrollment exists check: {exists}")
            
            # Test non-existent enrollment
            fake_exists = repo.exists("00000000-0000-0000-0000-000000000000")
            print(f"✅ Non-existent enrollment check: {fake_exists}")
            
        return True
        
    except Exception as e:
        print(f"❌ Enrollment repository error: {e}")
        return False


async def test_validation_service():
    """Test validation service."""
    print("\n🔍 Testing Validation Service...")
    print("=" * 40)
    
    try:
        # Create MongoDB service
        service = ValidationServiceFactory.create_mongo_service()
        print("✅ MongoDB validation service created")
        
        # Get an enrollment UUID for testing
        repo = MongoEnrollmentRepository()
        enrollment_uuids = repo.get_all_uuids()
        
        if not enrollment_uuids:
            print("⚠️  No enrollment UUIDs found for testing")
            return True
        
        test_uuid = enrollment_uuids[0]
        print(f"🎯 Testing with enrollment UUID: {test_uuid}")
        
        # Test validation initiation
        process = await service.initiate_validation(test_uuid)
        print(f"✅ Validation process created: {process.process_id}")
        print(f"   Status: {process.status}")
        print(f"   Enrollment UUID: {process.uuid_str}")
        
        # Wait a moment and check status
        await asyncio.sleep(3)
        
        updated_process = await service.get_validation_status(process.process_id)
        if updated_process:
            print(f"✅ Process status updated: {updated_process.status}")
        else:
            print("❌ Failed to retrieve process status")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Validation service error: {e}")
        return False


async def test_enrollment_collection():
    """Test direct enrollment collection access."""
    print("\n🔍 Testing Enrollment Collection...")
    print("=" * 40)
    
    try:
        collection = get_enrollment_collection()
        
        # Count documents
        count = collection.count_documents({})
        print(f"✅ Total enrollment documents: {count}")
        
        # Get a sample document
        sample_doc = collection.find_one({})
        if sample_doc:
            print("✅ Sample enrollment document found")
            print(f"   Document keys: {list(sample_doc.keys())}")
            
            # Check if uuid_str field exists
            if 'uuid_str' in sample_doc:
                print(f"   Sample uuid_str: {sample_doc['uuid_str']}")
            else:
                print("⚠️  No 'uuid_str' field found in document")
                print(f"   Available fields: {list(sample_doc.keys())}")
            
            # Check students_info
            if 'students_info' in sample_doc:
                students_count = len(sample_doc['students_info'])
                print(f"   Students in this enrollment: {students_count}")
            else:
                print("⚠️  No 'students_info' field found")
        else:
            print("⚠️  No enrollment documents found")
        
        return True
        
    except Exception as e:
        print(f"❌ Enrollment collection error: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Student Validation API - MongoDB Integration Test")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Enrollment Collection", test_enrollment_collection),
        ("Enrollment Repository", test_enrollment_repository),
        ("Validation Service", test_validation_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! MongoDB integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 