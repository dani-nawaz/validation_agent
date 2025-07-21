from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime, timezone
from api.models import ValidationProcess, ValidationStatus
from api.exceptions import EnrollmentNotFoundError, ValidationProcessNotFoundError
from api.database import get_enrollment_collection, DatabaseConnection
import logging

logger = logging.getLogger(__name__)


class EnrollmentRepository(ABC):
    """Abstract repository for enrollment data access."""
    
    @abstractmethod
    def get_by_uuid(self, uuid_str: str) -> Optional[Dict[str, Any]]:
        """Get enrollment by UUID."""
        pass
    
    @abstractmethod
    def exists(self, uuid_str: str) -> bool:
        """Check if enrollment exists."""
        pass
    
    @abstractmethod
    def get_all_uuids(self) -> List[str]:
        """Get all enrollment UUIDs."""
        pass





class MongoEnrollmentRepository(EnrollmentRepository):
    """MongoDB-based enrollment repository implementation."""
    
    def __init__(self):
        self.db_connection = DatabaseConnection.get_instance()
    
    def get_by_uuid(self, uuid_str: str) -> Optional[Dict[str, Any]]:
        """Get enrollment by UUID from MongoDB."""
        try:
            # Query enrollmentForm collection by uuid_str
            enrollment_collection = get_enrollment_collection()
            enrollment = enrollment_collection.find_one({"uuid_str": uuid_str})
            
            if enrollment:
                # Convert MongoDB document to dict and remove _id
                enrollment_dict = dict(enrollment)
                if '_id' in enrollment_dict:
                    del enrollment_dict['_id']
                return enrollment_dict
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving enrollment {uuid_str}: {e}")
            return None
    
    def exists(self, uuid_str: str) -> bool:
        """Check if enrollment exists in MongoDB."""
        return self.get_by_uuid(uuid_str) is not None
    
    def get_all_uuids(self) -> List[str]:
        """Get all enrollment UUIDs from MongoDB."""
        try:
            uuids = []
            
            # Get UUIDs from enrollmentForm collection
            enrollment_collection = get_enrollment_collection()
            enrollment_docs = enrollment_collection.find({}, {"uuid_str": 1, "_id": 0})
            for doc in enrollment_docs:
                if "uuid_str" in doc:
                    uuids.append(doc["uuid_str"])
            
            return uuids
            
        except Exception as e:
            logger.error(f"Error retrieving enrollment UUIDs: {e}")
            return []


class ValidationProcessRepository(ABC):
    """Abstract repository for validation process data access."""
    
    @abstractmethod
    def create(self, uuid_str: str, email: Optional[str] = None) -> ValidationProcess:
        """Create a new validation process."""
        pass
    
    @abstractmethod
    def get_by_id(self, process_id: str) -> Optional[ValidationProcess]:
        """Get validation process by ID."""
        pass
    
    @abstractmethod
    def update_status(
        self, 
        process_id: str, 
        status: ValidationStatus,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None
    ) -> ValidationProcess:
        """Update validation process status."""
        pass


class InMemoryValidationProcessRepository(ValidationProcessRepository):
    """In-memory validation process repository implementation."""
    
    def __init__(self):
        self._processes: Dict[str, ValidationProcess] = {}
    
    def create(self, uuid_str: str, email: Optional[str] = None) -> ValidationProcess:
        """Create a new validation process."""
        process_id = str(uuid.uuid4())
        process = ValidationProcess(
            process_id=process_id,
            uuid_str=uuid_str,
            email=email,
            status=ValidationStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        self._processes[process_id] = process
        return process
    
    def get_by_id(self, process_id: str) -> Optional[ValidationProcess]:
        """Get validation process by ID."""
        return self._processes.get(process_id)
    
    def update_status(
        self, 
        process_id: str, 
        status: ValidationStatus,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None
    ) -> ValidationProcess:
        """Update validation process status."""
        process = self.get_by_id(process_id)
        if not process:
            raise ValidationProcessNotFoundError(process_id)
        
        # Create updated process
        updated_process = ValidationProcess(
            process_id=process.process_id,
            uuid_str=process.uuid_str,
            email=process.email,
            status=status,
            created_at=process.created_at,
            updated_at=datetime.now(timezone.utc),
            error_message=error_message,
            result_data=result_data
        )
        
        self._processes[process_id] = updated_process
        return updated_process


class MongoValidationProcessRepository(ValidationProcessRepository):
    """MongoDB-based validation process repository implementation."""
    
    def __init__(self):
        self.db_connection = DatabaseConnection.get_instance()
        self.collection_name = 'validation_processes'
    
    def _get_collection(self):
        """Get validation processes collection."""
        return self.db_connection.get_collection(self.collection_name)
    
    def create(self, uuid_str: str, email: Optional[str] = None) -> ValidationProcess:
        """Create a new validation process in MongoDB."""
        try:
            process_id = str(uuid.uuid4())
            process = ValidationProcess(
                process_id=process_id,
                uuid_str=uuid_str,
                email=email,
                status=ValidationStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            
            # Convert to dict for MongoDB
            process_dict = {
                "process_id": process.process_id,
                "uuid_str": process.uuid_str,
                "email": process.email,
                "status": process.status.value,
                "created_at": process.created_at,
                "updated_at": process.updated_at,
                "error_message": process.error_message,
                "result_data": process.result_data
            }
            
            collection = self._get_collection()
            collection.insert_one(process_dict)
            
            return process
            
        except Exception as e:
            logger.error(f"Error creating validation process: {e}")
            raise
    
    def get_by_id(self, process_id: str) -> Optional[ValidationProcess]:
        """Get validation process by ID from MongoDB."""
        try:
            collection = self._get_collection()
            doc = collection.find_one({"process_id": process_id})
            
            if not doc:
                return None
            
            # Convert MongoDB document to ValidationProcess
            return ValidationProcess(
                process_id=doc["process_id"],
                uuid_str=doc["uuid_str"],
                email=doc.get("email"),
                status=ValidationStatus(doc["status"]),
                created_at=doc["created_at"],
                updated_at=doc.get("updated_at"),
                error_message=doc.get("error_message"),
                result_data=doc.get("result_data")
            )
            
        except Exception as e:
            logger.error(f"Error retrieving validation process {process_id}: {e}")
            return None
    
    def update_status(
        self, 
        process_id: str, 
        status: ValidationStatus,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None
    ) -> ValidationProcess:
        """Update validation process status in MongoDB."""
        try:
            collection = self._get_collection()
            
            # Get existing process
            existing_doc = collection.find_one({"process_id": process_id})
            if not existing_doc:
                raise ValidationProcessNotFoundError(process_id)
            
            # Prepare update data
            update_data = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if error_message is not None:
                update_data["error_message"] = error_message
            
            if result_data is not None:
                update_data["result_data"] = result_data
            
            # Update in MongoDB
            collection.update_one(
                {"process_id": process_id},
                {"$set": update_data}
            )
            
            # Return updated process
            updated_doc = collection.find_one({"process_id": process_id})
            
            return ValidationProcess(
                process_id=updated_doc["process_id"],
                uuid_str=updated_doc["uuid_str"],
                email=updated_doc.get("email"),
                status=ValidationStatus(updated_doc["status"]),
                created_at=updated_doc["created_at"],
                updated_at=updated_doc.get("updated_at"),
                error_message=updated_doc.get("error_message"),
                result_data=updated_doc.get("result_data")
            )
            
        except ValidationProcessNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating validation process {process_id}: {e}")
            raise 