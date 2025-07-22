import os
import base64
import json
import requests
import tempfile
from typing import Dict, Any, Optional, List
from PIL import Image
from openai import OpenAI
from student_mongodb_tools import get_student_by_id, get_all_student_ids, update_student

def download_image_from_url(url: str) -> str:
    """
    Download an image from URL (S3) to a temporary file.
    
    Args:
        url: S3 URL of the image
        
    Returns:
        Path to the temporary file
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            return tmp_file.name
    except Exception as e:
        raise Exception(f"Error downloading image from URL: {e}")

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_local_birth_certificate_path(student_id: str) -> Optional[str]:
    """
    Check if a local birth certificate exists for the student.
    Handles both UUID and STU### formats.
    
    Args:
        student_id: Student ID (UUID or STU### format)
        
    Returns:
        Path to local birth certificate if exists, None otherwise
    """
    # Try different possible paths
    possible_paths = []
    
    # For UUID, try to find a mapping file or use STU### format
    # For now, we'll check for STU### files as a fallback
    base_dir = os.path.join(os.path.dirname(__file__), "docs")
    
    # Check if docs directory exists
    if not os.path.exists(base_dir):
        base_dir = "docs"  # Try relative path
    
    # If it's a UUID, we might need to map it to STU### format
    # For now, let's check for common patterns
    if "-" in student_id:  # UUID format
        # Try STU001, STU002, etc. as examples
        # In a real system, you'd have a mapping
        for i in range(1, 10):
            possible_paths.append(os.path.join(base_dir, f"STU{i:03d}.png"))
    else:
        # Direct STU### format
        possible_paths.append(os.path.join(base_dir, f"{student_id}.png"))
    
    # Also try the exact student_id as filename
    possible_paths.append(os.path.join(base_dir, f"{student_id}.png"))
    
    # Check each possible path
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

def extract_data_from_birth_certificate(image_source: str, prefer_local: bool = True) -> Dict[str, Any]:
    """
    Use GPT Vision to extract structured data from a birth certificate image.
    
    Args:
        image_source: Either a local file path, S3 URL, or student ID
        prefer_local: If True, check for local files first when given a student ID
        
    Returns:
        Dictionary containing extracted data
    """
    image_path = None
    is_temp = False
    
    # First check if it's a direct local file path
    if os.path.exists(image_source):
        image_path = image_source
    elif prefer_local and not image_source.startswith('http'):
        # Try to find local birth certificate
        local_path = get_local_birth_certificate_path(image_source)
        if local_path:
            image_path = local_path
            print(f"Using local birth certificate: {image_path}")
    
    # If no local file found and it's a URL, download it
    if not image_path and image_source.startswith('http'):
        image_path = download_image_from_url(image_source)
        is_temp = True
    
    if not image_path:
        raise FileNotFoundError(f"No birth certificate found for: {image_source}")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Please extract the following information from this birth certificate image and return it as a JSON object:

{
  "name": "Full name as it appears on the certificate",
  "first_name": "First name only",
  "last_name": "Last name only",
  "date_of_birth": "Date of birth in YYYY-MM-DD format",
  "place_of_birth": "Place of birth",
  "father_name": "Father's name",
  "mother_name": "Mother's name",
  "gender": "Gender",
  "certificate_number": "Certificate number if available",
  "registration_date": "Registration date if available in YYYY-MM-DD format"
}

If any field is not clearly visible or not present, use null for that field. Be very careful to extract the exact text as it appears."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Parse the JSON response
        content = response.choices[0].message.content
        
        # Clean up the response to extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        extracted_data = json.loads(content.strip())
        return extracted_data
        
    finally:
        # Clean up temporary file if we downloaded it
        if is_temp and image_path and os.path.exists(image_path):
            os.unlink(image_path)

def compare_student_data(student_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare MongoDB student data with extracted birth certificate data to find anomalies.
    Args:
        student_id: Student ID (UUID string) to look up in MongoDB
        extracted_data: Data extracted from birth certificate
    Returns:
        Dictionary containing comparison results and anomalies
    """
    # Get student record from MongoDB
    mongodb_record = get_student_by_id(student_id)
    if mongodb_record is None:
        return {
            "status": "error",
            "message": f"Student ID {student_id} not found in MongoDB"
        }

    anomalies = []
    matches = []
    additional_info = {}

    # Compare all fields present in extracted_data
    for key, cert_value in extracted_data.items():
        db_value = mongodb_record.get(key)
        if db_value is not None:
            # Normalize for comparison (case-insensitive, strip whitespace)
            if isinstance(cert_value, str) and isinstance(db_value, str):
                cert_val_norm = cert_value.strip().lower()
                db_val_norm = db_value.strip().lower()
            else:
                cert_val_norm = cert_value
                db_val_norm = db_value
            if cert_val_norm != db_val_norm:
                anomalies.append({
                    "field": key,
                    "mongodb_value": db_value,
                    "certificate_value": cert_value,
                    "type": "mismatch"
                })
            else:
                matches.append({
                    "field": key,
                    "value": db_value
                })
        else:
            # Field is not in DB record, treat as additional info
            additional_info[key] = cert_value

    return {
        "status": "success",
        "mongodb_record": mongodb_record,
        "certificate_data": extracted_data,
        "matches": matches,
        "anomalies": anomalies,
        "additional_info": additional_info,
        "total_anomalies": len(anomalies)
    }

def update_mongodb_record(student_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a student record in MongoDB.
    
    Args:
        student_id: Student ID (UUID string) to update
        updates: Dictionary of field updates
        
    Returns:
        Result of the update operation
    """
    # Use the update_student function from student_mongodb_tools
    return update_student(student_id, updates)

def get_birth_certificate_url(student_id: str) -> Optional[str]:
    """
    Get the S3 URL of a student's birth certificate from MongoDB.
    
    Args:
        student_id: Student ID (UUID string)
        
    Returns:
        S3 URL of the birth certificate or None if not found
    """
    student_record = get_student_by_id(student_id)
    
    if not student_record:
        return None
    
    documents = student_record.get('documents', {})
    birth_cert = documents.get('birth_certificate', {})
    
    return birth_cert.get('s3_url')

def get_birth_certificate_source(student_id: str, prefer_local: bool = True) -> Optional[str]:
    """
    Get the birth certificate source for a student.
    Checks local files first if prefer_local is True, then falls back to S3.
    
    Args:
        student_id: Student ID (UUID string)
        prefer_local: If True, prefer local files over S3
        
    Returns:
        Path to local file or S3 URL, or None if not found
    """
    if prefer_local:
        # Check for local file first
        local_path = get_local_birth_certificate_path(student_id)
        if local_path:
            return local_path
    
    # Fall back to S3 URL
    return get_birth_certificate_url(student_id)

def validate_image_file(image_path: str) -> bool:
    """
    Validate if the provided path is a valid image file or URL.
    
    Args:
        image_path: Path or URL to check
        
    Returns:
        True if valid image file/URL, False otherwise
    """
    # Check if it's a local file
    if os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                return img.format.lower() in ['png', 'jpg', 'jpeg']
        except:
            return False
    
    # Check if it's a URL
    if image_path.startswith('http'):
        try:
            response = requests.head(image_path)
            return response.status_code == 200
        except:
            return False
    
    # Check if we can find a local birth certificate for this ID
    local_path = get_local_birth_certificate_path(image_path)
    if local_path:
        return validate_image_file(local_path)
    
    return False 