import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List
from api.database import get_enrollment_collection
import logging
from bson import Binary
import uuid

logger = logging.getLogger(__name__)

def binary_to_uuid_string(binary_obj) -> str:
    """
    Convert a Binary UUID object to a string UUID.
    
    Args:
        binary_obj: Binary UUID object from MongoDB
        
    Returns:
        String representation of the UUID
    """
    try:
        if isinstance(binary_obj, Binary):
            # For Binary objects, we can access the bytes directly
            return str(uuid.UUID(bytes=binary_obj))
        else:
            # If it's already a string or other format
            return str(binary_obj)
    except Exception as e:
        logger.error(f"Error converting Binary to UUID string: {e}")
        return None


def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch student record by ID from MongoDB.
    Now searches within the students_info array of enrollment documents.
    
    Args:
        student_id: The student ID (UUID string) to search for
        
    Returns:
        Dictionary containing student information if found, None otherwise
    """
    print(f"DEBUG: get_student_by_id called with student_id: {student_id}")
    
    try:
        print(f"DEBUG: Getting enrollment collection...")
        collection = get_enrollment_collection()
        print(f"DEBUG: Collection obtained successfully")
        
        parent_doc = collection.find_one({
            "uuid_str": student_id
        })
        
        if parent_doc and 'students_info' in parent_doc:
            # Find the specific student within the array
            for i, student in enumerate(parent_doc['students_info']):
                
                student_record = {
                    'student_id': student_id,
                    'first_name': student.get('first_name', ''),
                    'last_name': student.get('last_name', ''),
                    'name': f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
                    'email': parent_doc.get('email', ''),
                    'phone': parent_doc.get('phone', ''),
                    'birthdate': student.get('birthdate', ''),
                    'gender': student.get('gender', ''),
                    'address': student.get('address', {}),
                    'applying_grade': student.get('application_info', {}).get('applyingGrade', ''),
                    'documents': student.get('documents', {}),
                    'parent_doc_id': str(parent_doc.get('_id', ''))
                }
                print(f"DEBUG: ✅ Returning student record for: {student_record['name']}")
                return student_record
    
        print(f"DEBUG: ❌ Student {student_id} not found in any document")
        return None
        
    except Exception as e:
        print(f"DEBUG: ❌ Exception in get_student_by_id: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_uuid_format(student_id: str) -> bool:
    """
    Validate if the provided string is a valid UUID.
    
    Args:
        student_id: The ID to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    try:
        uuid.UUID(student_id)
        return True
    except (ValueError, AttributeError):
        return False

def validate_student_id_format(student_id: str) -> bool:
    """
    Validate if student ID is either a valid UUID or follows STU### format.
    
    Args:
        student_id: The student ID to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    if not student_id:
        return False
    
    # Check if it's a valid UUID
    if validate_uuid_format(student_id):
        return True
    
    # Check legacy STU### format
    return (len(student_id) == 6 and 
            student_id.startswith("STU") and 
            student_id[3:].isdigit())

def get_all_student_ids() -> List[str]:
    """
    Get list of all available student IDs from MongoDB.
    
    Returns:
        List of all student IDs (UUIDs as strings)
    """
    try:
        collection = get_enrollment_collection()
        
        # Get all enrollment documents
        all_students = []
        
        for doc in collection.find({}, {"students_info.id": 1, "students_info.first_name": 1, "students_info.last_name": 1}):
            if 'students_info' in doc:
                for student in doc['students_info']:
                    student_id_binary = student.get('id')
                    if student_id_binary:
                        # Convert Binary UUID to string
                        student_uuid_str = binary_to_uuid_string(student_id_binary)
                        
                        if student_uuid_str:
                            # Include name for better identification
                            first_name = student.get('first_name', '')
                            last_name = student.get('last_name', '')
                            display_name = f"{student_uuid_str} ({first_name} {last_name})".strip()
                            
                            all_students.append(display_name)
        
        return sorted(all_students)
        
    except Exception as e:
        logger.error(f"Error reading student IDs from MongoDB: {e}")
        return []

def create_student(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new student record in MongoDB.
    
    Args:
        student_data: Dictionary containing student information
        
    Returns:
        Result of the operation
    """
    try:
        collection = get_enrollment_collection()
        
        # Validate student_id format
        student_id = student_data.get("student_id")
        if not validate_student_id_format(student_id):
            return {
                "status": "error",
                "message": f"Invalid student ID format: {student_id}. Expected format: STU### (e.g., STU001)"
            }
        
        # Check if student already exists
        if get_student_by_id(student_id):
            return {
                "status": "error",
                "message": f"Student with ID {student_id} already exists"
            }
        
        # Insert the student
        result = collection.insert_one(student_data)
        
        return {
            "status": "success",
            "message": f"Student {student_id} created successfully",
            "inserted_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Error creating student in MongoDB: {e}")
        return {
            "status": "error",
            "message": f"Error creating student: {e}"
        }

def update_student(student_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a student record in MongoDB.
    Updates fields within the students_info array.
    
    Args:
        student_id: Student ID (UUID string) to update (parent uuid_str)
        updates: Dictionary of field updates
        
    Returns:
        Result of the update operation
    """
    try:
        collection = get_enrollment_collection()
        
        # Get the current student record to find parent document
        parent_doc = collection.find_one({"uuid_str": student_id})
        print(f"DEBUG: Parent document: {parent_doc}")
        if not parent_doc or "students_info" not in parent_doc:
            return {
                "status": "error",
                "message": f"Parent document with uuid_str {student_id} not found or has no students_info"
            }
        
        # Find the correct student in students_info
        students = parent_doc["students_info"]
        print(f"DEBUG: Students: {students}")

        if not students:
            return {
                "status": "error",
                "message": f"No students found in students_info for parent {student_id}"
            }
        # For now, update the first student (or you can add logic to match by name, etc.)
        student = students[0]
        student_uuid = student["id"]  # This is a Binary UUID
        print(f"DEBUG: Will update student with Binary UUID: {student_uuid}")
        
        # Define valid fields
        parent_fields = {"email", "phone"}
        student_fields = {
            "first_name", "last_name", "birthdate", "gender", "address", "has_mailing_address",
            "mailing_address", "info_status", "step_completed", "created_at", "updated_at",
            "application_info", "medical_info", "care_giver_info", "special_assistance_info", "documents"
        }
        
        # Map our simplified field names to the actual MongoDB structure
        field_mapping = {
            'first_name': 'students_info.$.first_name',
            'last_name': 'students_info.$.last_name',
            'birthdate': 'students_info.$.birthdate',
            'gender': 'students_info.$.gender',
            'address': 'students_info.$.address',
            'has_mailing_address': 'students_info.$.has_mailing_address',
            'mailing_address': 'students_info.$.mailing_address',
            'info_status': 'students_info.$.info_status',
            'step_completed': 'students_info.$.step_completed',
            'created_at': 'students_info.$.created_at',
            'updated_at': 'students_info.$.updated_at',
            'application_info': 'students_info.$.application_info',
            'medical_info': 'students_info.$.medical_info',
            'care_giver_info': 'students_info.$.care_giver_info',
            'special_assistance_info': 'students_info.$.special_assistance_info',
            'documents': 'students_info.$.documents',
        }
        
        parent_updates = {}
        student_updates = {}
        ignored_fields = []
        
        for field, new_value in updates.items():
            if field in parent_fields:
                parent_updates[field] = new_value
            elif field in student_fields:
                student_updates[field_mapping[field]] = new_value
            elif field == 'name':
                # Split name into first and last name
                name_parts = new_value.strip().split(' ', 1)
                student_updates['students_info.$.first_name'] = name_parts[0]
                if len(name_parts) > 1:
                    student_updates['students_info.$.last_name'] = name_parts[1]
                else:
                    student_updates['students_info.$.last_name'] = ''
            else:
                ignored_fields.append(field)
        
        if ignored_fields:
            print(f"Ignored fields (not in schema): {ignored_fields}")
        
        # Apply updates
        modified_count = 0
        
        if student_updates:
            print(f"DEBUG: Updating student {student_id} (student_info.id={student_uuid}) with updates: {student_updates}")
            result = collection.update_one(
                {"uuid_str": student_id, "students_info.id": student_uuid},
                {"$set": student_updates}
            )
            print(f"DEBUG: MongoDB update result: {result.raw_result}")
            modified_count += result.modified_count
        
        if parent_updates:
            print(f"DEBUG: Updating parent document {parent_doc.get('_id')} with updates: {parent_updates}")
            result = collection.update_one(
                {"_id": parent_doc.get('_id')},
                {"$set": parent_updates}
            )
            print(f"DEBUG: MongoDB parent update result: {result.raw_result}")
            modified_count += result.modified_count
        
        if modified_count > 0:
            return {
                "status": "success",
                "message": f"Successfully updated student {student_id}",
                "modified_count": modified_count,
                "updates": {**parent_updates, **student_updates}
            }
        else:
            return {
                "status": "success",
                "message": "No changes were made (values might be the same or fields not found)",
                "modified_count": 0
            }
        
    except Exception as e:
        logger.error(f"Error updating student in MongoDB: {e}")
        return {
            "status": "error",
            "message": f"Error updating student: {e}"
        } 