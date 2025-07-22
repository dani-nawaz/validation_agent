#!/usr/bin/env python3
"""
Simple MongoDB test to check connection and see available databases/collections.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

def simple_mongodb_test():
    """Simple test to check MongoDB connection and structure."""
    print("Simple MongoDB Test")
    print("==================")
    
    # Check environment
    mongodb_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME")
    
    print(f"MONGODB_URI: {mongodb_uri}")
    print(f"DB_NAME: {db_name}")
    
    if not mongodb_uri:
        print("❌ MONGODB_URI not set!")
        return
    
    try:
        # Connect to MongoDB
        print("\n1. Connecting to MongoDB...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List all databases
        print("\n2. Available databases:")
        databases = client.list_database_names()
        for db in databases:
            print(f"   - {db}")
        
        # If DB_NAME is not set, try to guess from URI
        if not db_name:
            print("\n⚠️  DB_NAME not set, trying to extract from URI...")
            # Try to extract database name from URI
            if '/' in mongodb_uri:
                db_name = mongodb_uri.split('/')[-1].split('?')[0]
                print(f"   Extracted DB_NAME: {db_name}")
        
        if db_name and db_name in databases:
            print(f"\n3. Using database: {db_name}")
            db = client[db_name]
            
            # List collections
            print("   Available collections:")
            collections = db.list_collection_names()
            for collection in collections:
                print(f"     - {collection}")
            
            # Check enrollmentForm collection
            if 'enrollmentForm' in collections:
                print(f"\n4. Checking enrollmentForm collection...")
                collection = db['enrollmentForm']
                doc_count = collection.count_documents({})
                print(f"   Document count: {doc_count}")
                
                if doc_count > 0:
                    # Get first document
                    first_doc = collection.find_one({})
                    print(f"   First document keys: {list(first_doc.keys())}")
                    
                    # Check for students_info
                    if 'students_info' in first_doc:
                        students_info = first_doc['students_info']
                        print(f"   students_info count: {len(students_info)}")
                        
                        if students_info:
                            first_student = students_info[0]
                            print(f"   First student keys: {list(first_student.keys())}")
                            
                            # Check for UUID fields
                            if 'uuid_str' in first_student:
                                print(f"   uuid_str: {first_student['uuid_str']}")
                            if 'id' in first_student:
                                print(f"   id: {first_student['id']} (type: {type(first_student['id'])})")
                    else:
                        print("   ❌ No students_info found in document")
                else:
                    print("   ❌ No documents in enrollmentForm collection")
            else:
                print("   ❌ enrollmentForm collection not found")
        else:
            print(f"❌ Database '{db_name}' not found in available databases")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_mongodb_test() 