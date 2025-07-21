from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Singleton MongoDB connection manager."""
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        """Get singleton instance of database connection."""
        if cls._instance is None:
            cls._instance = DatabaseConnection()
        return cls._instance

    def __init__(self):
        """Initialize database connection configuration."""
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI from environment variable or use default
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('DB_NAME')

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            if not self._client:
                self._client = MongoClient(
                    self.mongodb_uri, 
                    serverSelectionTimeoutMS=5000
                )
                # Verify connection
                self._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
            return self._client
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB server: {e}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"Server selection timeout - check if MongoDB is running: {e}")
            raise

    def get_database(self):
        """Get database instance."""
        if not self._client:
            self.connect()
        return self._client[self.db_name]

    def get_collection(self, collection_name: str):
        """Get collection from database."""
        db = self.get_database()
        return db[collection_name]

    def close_connection(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        """Check if database connection is active."""
        try:
            if self._client:
                self._client.admin.command('ping')
                return True
        except Exception:
            pass
        return False


def get_enrollment_collection():
    """Helper function to get enrollment collection."""
    db = DatabaseConnection.get_instance()
    return db.get_collection('enrollmentForm')


def get_students_collection():
    """Helper function to get students collection."""
    db = DatabaseConnection.get_instance()
    return db.get_collection('students')


# Example usage and test function
def test_connection():
    """Test database connection."""
    try:
        # Get enrollment collection
        collection = get_enrollment_collection()
        
        # Test the connection with a simple query
        doc_count = collection.count_documents({})
        logger.info(f"Successfully connected. Found {doc_count} documents in enrollmentForm.")
        
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
    finally:
        # Close the connection
        DatabaseConnection.get_instance().close_connection()


if __name__ == '__main__':
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    success = test_connection()
    if success:
        print("✅ Database connection test passed")
    else:
        print("❌ Database connection test failed") 