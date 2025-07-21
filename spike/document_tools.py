import os
import base64
import json
from typing import Dict, Any, Optional, List
from PIL import Image
import pandas as pd
from openai import OpenAI
from student_tools import get_student_by_id, get_all_student_ids

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

def extract_data_from_birth_certificate(image_path: str) -> Dict[str, Any]:
    """
    Use GPT Vision to extract structured data from a birth certificate image.
    
    Args:
        image_path: Path to the birth certificate PNG file
        
    Returns:
        Dictionary containing extracted data
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Encode image to base64
    base64_image = encode_image_to_base64(image_path)
    
    try:
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
  "date_of_birth": "Date of birth in YYYY-MM-DD format",
  "place_of_birth": "Place of birth",
  "father_name": "Father's name",
  "mother_name": "Mother's name",
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
        
    except Exception as e:
        raise Exception(f"Error extracting data from birth certificate: {e}")

def compare_student_data(student_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare CSV student data with extracted birth certificate data to find anomalies.
    
    Args:
        student_id: Student ID to look up in CSV
        extracted_data: Data extracted from birth certificate
        
    Returns:
        Dictionary containing comparison results and anomalies
    """
    # Get student record from CSV
    csv_record = get_student_by_id(student_id)
    
    if csv_record is None:
        return {
            "status": "error",
            "message": f"Student ID {student_id} not found in CSV database"
        }
    
    # Define mappings between CSV fields and birth certificate fields
    field_mappings = {
        "name": "name",  # CSV 'name' vs birth certificate 'name'
    }
    
    anomalies = []
    matches = []
    
    # Compare name
    csv_name = csv_record.get('name', '').strip().lower()
    cert_name = extracted_data.get('name', '').strip().lower()
    
    if csv_name and cert_name:
        if csv_name != cert_name:
            anomalies.append({
                "field": "name",
                "csv_value": csv_record.get('name'),
                "certificate_value": extracted_data.get('name'),
                "type": "mismatch"
            })
        else:
            matches.append({
                "field": "name",
                "value": csv_record.get('name')
            })
    
    # Check for additional information from birth certificate
    additional_info = {}
    for key, value in extracted_data.items():
        if key not in ["name"] and value is not None:
            additional_info[key] = value
    
    return {
        "status": "success",
        "csv_record": csv_record,
        "certificate_data": extracted_data,
        "matches": matches,
        "anomalies": anomalies,
        "additional_info": additional_info,
        "total_anomalies": len(anomalies)
    }

def update_csv_record(student_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a student record in the CSV file.
    
    Args:
        student_id: Student ID to update
        updates: Dictionary of field updates
        
    Returns:
        Result of the update operation
    """
    csv_path = "students.csv"
    
    try:
        # Load the CSV
        df = pd.read_csv(csv_path)
        
        # Find the student record
        df['student_id'] = df['student_id'].astype(str)
        student_index = df[df['student_id'] == student_id].index
        
        if len(student_index) == 0:
            return {
                "status": "error",
                "message": f"Student ID {student_id} not found in CSV"
            }
        
        # Apply updates
        updated_fields = []
        for field, new_value in updates.items():
            if field in df.columns:
                old_value = df.loc[student_index[0], field]
                df.loc[student_index[0], field] = new_value
                updated_fields.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value
                })
        
        # Save the updated CSV
        df.to_csv(csv_path, index=False)
        
        return {
            "status": "success",
            "message": f"Successfully updated {len(updated_fields)} field(s) for student {student_id}",
            "updated_fields": updated_fields
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating CSV: {e}"
        }

def validate_image_file(image_path: str) -> bool:
    """
    Validate if the provided path is a valid image file.
    
    Args:
        image_path: Path to check
        
    Returns:
        True if valid image file, False otherwise
    """
    if not os.path.exists(image_path):
        return False
    
    try:
        with Image.open(image_path) as img:
            return img.format.lower() in ['png', 'jpg', 'jpeg']
    except:
        return False 