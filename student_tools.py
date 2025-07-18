import pandas as pd
import os
from typing import Optional, Dict, Any
from database import get_enrollement_collection_from_db

def load_student_data(csv_path: str = "students.csv") -> pd.DataFrame:
    """Load student data from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Student CSV file not found: {csv_path}")
    
    return pd.read_csv(csv_path)

def get_student_by_id(student_id: str, csv_path: str = "students.csv") -> Optional[Dict[str, Any]]:
    """
    Fetch student record by ID from CSV file.
    
    Args:
        student_id: The student ID to search for
        csv_path: Path to the CSV file containing student data
        
    Returns:
        Dictionary containing student information if found, None otherwise
    """
    try:
        df = load_student_data(csv_path)
        
        # Convert student_id column to string for comparison
        df['student_id'] = df['student_id'].astype(str)
        
        # Search for the student
        student_row = df[df['student_id'] == student_id]
        
        if student_row.empty:
            return None
        
        # Convert to dictionary and return first match
        return student_row.iloc[0].to_dict()
        
    except Exception as e:
        print(f"Error reading student data: {e}")
        return None

def get_student_from_db_by_id(student_id: str): 

    """
    Fetch student record by ID from MongoDB.
    
    Args:
        student_id: The student ID to search for
        
    Returns:
        Dictionary containing student information if found, None otherwise
    """    
    try:
        enrollment_collection = get_enrollement_collection_from_db()
        student = enrollment_collection.find_one({"uuid_str": student_id})
        if student:
            return student
        return None
    except Exception as e:
        print(f"Error fetching student from database: {e}")
        return None
def validate_student_id_format(student_id: str) -> bool:
    """
    Validate if student ID follows the expected format (STU + 3 digits).
    
    Args:
        student_id: The student ID to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    if not student_id:
        return False
    
    return (len(student_id) == 6 and 
            student_id.startswith("STU") and 
            student_id[3:].isdigit())

def get_all_student_ids(csv_path: str = "students.csv") -> list:
    """
    Get list of all available student IDs.
    
    Args:
        csv_path: Path to the CSV file containing student data
        
    Returns:
        List of all student IDs
    """
    try:
        df = load_student_data(csv_path)
        return df['student_id'].astype(str).tolist()
    except Exception as e:
        print(f"Error reading student data: {e}")
        return [] 