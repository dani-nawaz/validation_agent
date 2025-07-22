#!/usr/bin/env python3
"""
Script to help set up environment variables for MongoDB connection.
"""

import os

def setup_environment():
    """Help set up environment variables."""
    print("MongoDB Environment Setup")
    print("========================")
    print()
    print("You need to create a .env file with your MongoDB connection details.")
    print()
    print("Based on your student record, you have a MongoDB instance with enrollment data.")
    print()
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if os.path.exists(env_file):
        print(f"✅ .env file exists at: {env_file}")
        print("Current contents:")
        with open(env_file, 'r') as f:
            print(f.read())
    else:
        print(f"❌ .env file not found at: {env_file}")
        print()
        print("Please create a .env file with the following variables:")
        print()
        print("# MongoDB Configuration")
        print("MONGODB_URI=mongodb://your-mongodb-host:27017/your_database")
        print("DB_NAME=your_database_name")
        print()
        print("# OpenAI Configuration")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        print()
        print("Example .env file content:")
        print("=" * 50)
        print("MONGODB_URI=mongodb://localhost:27017/enrollment_db")
        print("DB_NAME=enrollment_db")
        print("OPENAI_API_KEY=sk-your-openai-api-key")
        print("=" * 50)
        print()
        print("To create the .env file:")
        print("1. Copy the example content above")
        print("2. Replace with your actual MongoDB connection details")
        print("3. Save as '.env' in the project root directory")
        print()
        print("Common MongoDB URI formats:")
        print("- Local MongoDB: mongodb://localhost:27017/database_name")
        print("- MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/database_name")
        print("- MongoDB with auth: mongodb://username:password@host:27017/database_name")

def test_connection_with_env():
    """Test connection if .env file exists."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_file):
        print("❌ .env file not found. Please create it first.")
        return
    
    print("\nTesting connection with .env file...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME")
    
    if not mongodb_uri:
        print("❌ MONGODB_URI not set in .env file")
        return
    
    if not db_name:
        print("❌ DB_NAME not set in .env file")
        return
    
    print(f"✅ MONGODB_URI: {mongodb_uri}")
    print(f"✅ DB_NAME: {db_name}")
    
    try:
        from pymongo import MongoClient
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"✅ Database '{db_name}' accessible")
        print(f"   Collections: {collections}")
        
        if 'enrollmentForm' in collections:
            collection = db['enrollmentForm']
            doc_count = collection.count_documents({})
            print(f"✅ enrollmentForm collection found with {doc_count} documents")
        else:
            print("⚠️  enrollmentForm collection not found")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    setup_environment()
    test_connection_with_env() 