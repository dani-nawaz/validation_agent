# from student_mongodb_tools import get_student_by_id
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any
import uuid
from bson import Binary
from api.database import get_enrollment_collection


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
        print(f"Error converting Binary to UUID string: {e}")
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


if __name__ == "__main__":
    # Test with a sample UUID
    test_uuid = "ebbd816b-6191-11f0-9ec4-a134ade00957"
    # test_uuid = "1ef47dda-5884-422b-b84b-2ee3d119b0c7"
    print(f"Testing student lookup for: {test_uuid}")
    result = get_student_by_id(test_uuid)
    
    if result:
        print(f"✅ Found student: {result.get('name')}")
        print(f"   Email: {result.get('email')}")
        print(f"   Phone: {result.get('phone')}")
        print(result)
    else:
        print("❌ Student not found")
    
    print("done")