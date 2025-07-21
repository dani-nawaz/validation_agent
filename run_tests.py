#!/usr/bin/env python3
"""
Test runner for Student Validation API.

Runs all available tests in sequence and provides a summary.
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime

def run_test_script(script_name: str, description: str) -> bool:
    """Run a test script and return True if successful."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"Script: {script_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True,
                              timeout=120)  # 2 minute timeout
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 120 seconds")
        return False
    except FileNotFoundError:
        print(f"❌ Test script {script_name} not found")
        return False
    except Exception as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking Prerequisites...")
    
    issues = []
    
    # Check if required test files exist
    test_files = [
        "test_api.py",
        "test_uuid_validation.py",
        "api/database.py"
    ]
    
    for file in test_files:
        if not os.path.exists(file):
            issues.append(f"Missing test file: {file}")
        else:
            print(f"✅ Found {file}")
    
    # Check MongoDB environment
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        print("✅ MONGODB_URI is configured")
    else:
        print("⚠️  MONGODB_URI not set, using default")
    
    if issues:
        print("\n❌ Prerequisites not met:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    
    print("✅ All prerequisites met")
    return True

def main():
    """Main test runner function."""
    print("🚀 Student Validation API - Test Suite Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Exiting due to missing prerequisites")
        sys.exit(1)
    
    # Define test suite
    tests = [
        ("api/database.py", "Database Connection Test"),
        ("test_api.py", "MongoDB Integration Tests"),
        ("test_uuid_validation.py", "UUID Validation Tests"),
    ]
    
    results = []
    start_time = datetime.now()
    
    # Run all tests
    for script, description in tests:
        success = run_test_script(script, description)
        results.append((description, success))
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Suite Summary")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Duration: {duration.total_seconds():.1f} seconds")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
    
    if passed_tests == total_tests:
        print("\n🎉 All test suites passed! The API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed_tests} test suite(s) failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 