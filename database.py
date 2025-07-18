from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

class DatabaseConnection:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseConnection()
        return cls._instance

    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI from environment variable or use default
        self.mongodb_uri = os.getenv('MONGODB_URI', 
            "mongodb://admin:%40uditP%4055w0rd@34.221.247.48/admin")
        self.db_name = os.getenv('DB_NAME', 'lifetechacademy')

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            if not self._client:
                self._client = MongoClient(self.mongodb_uri, 
                    serverSelectionTimeoutMS=5000)
                # Verify connection
                self._client.admin.command('ping')
                print("Successfully connected to MongoDB")
            return self._client
        except ConnectionFailure:
            print("Failed to connect to MongoDB server")
            raise
        except ServerSelectionTimeoutError:
            print("Server selection timeout - check if MongoDB is running")
            raise

    def get_database(self):
        """Get database instance"""
        if not self._client:
            self.connect()
        return self._client[self.db_name]

    def get_collection(self, collection_name):
        """Get collection from database"""
        db = self.get_database()
        return db[collection_name]

    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            print("MongoDB connection closed")

def get_enrollment_collection():
    """Helper function to get enrollment collection"""
    db = DatabaseConnection.get_instance()
    return db.get_collection('enrollmentForm')

# Example usage
if __name__ == '__main__':
    try:
        # Get enrollment collection
        collection = get_enrollment_collection()
        
        # Test the connection with a simple query
        doc_count = collection.count_documents({})
        print(f"Successfully connected. Found {doc_count} documents.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the connection
        DatabaseConnection.get_instance().close_connection()