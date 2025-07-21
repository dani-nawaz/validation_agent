#!/usr/bin/env python3
"""
Student Validation API Startup Script

This script starts the FastAPI application for the student validation service.
"""

import os
import sys
import uvicorn
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import pandas
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if the environment is properly set up."""
    issues = []
    
    # Check MongoDB configuration
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        print("✅ MONGODB_URI is configured")
    else:
        print("⚠️  MONGODB_URI not set, will use default")
    
    # MongoDB is the only backend in production
    print("✅ Production mode - MongoDB only backend")
    
    # Check if OpenAI API key is set (optional for basic validation)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set (required for advanced document validation)")
    else:
        print("✅ OPENAI_API_KEY is set")
    
    # Production uses MongoDB only
    print("✅ MongoDB backend (production configuration)")
    
    return issues

def main():
    """Main function to start the API server."""
    print("🚀 Starting Student Validation API")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    issues = check_environment()
    if issues:
        print("\n⚠️  Environment issues detected:")
        for issue in issues:
            print(f"   {issue}")
        print("\nAPI will start but some features may not work properly.")
    
    print("\n📚 API Documentation will be available at:")
    print("   • Swagger UI: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    print("\n🎯 API Endpoints:")
    print("   • POST /api/validate - Initiate validation")
    print("   • GET /api/validate/{process_id} - Get validation status")
    print("   • GET /health - Health check")
    
    print("\n⚙️  Configuration:")
    print("   • Database: MongoDB (Production)")
    print(f"   • MongoDB URI: {os.getenv('MONGODB_URI', 'Default')}")
    print(f"   • Database Name: {os.getenv('DB_NAME', 'lifetechacademy')}")
    
    print("\n🔄 Starting server...")
    
    try:
        uvicorn.run(
            "api.main:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            reload=os.getenv("RELOAD", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 