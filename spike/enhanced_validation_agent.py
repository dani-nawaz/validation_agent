import os
import asyncio
import json
from pydantic import BaseModel
from agents import Agent, Runner, function_tool, RunContextWrapper
from student_mongodb_tools import get_student_by_id, validate_student_id_format, get_all_student_ids
from document_mongodb_tools import (
    extract_data_from_birth_certificate,
    compare_student_data,
    update_mongodb_record,
    get_birth_certificate_url,
    get_birth_certificate_source,
    validate_image_file
)

from dotenv import load_dotenv
load_dotenv()

# Enhanced context for the validation agent
class EnhancedValidationContext(BaseModel):
    last_student_id: str | None = None
    pending_updates: dict | None = None
    document_data: dict | None = None

# Enhanced tool functions using the proper decorator
@function_tool
async def fetch_student_record(student_id: str) -> str:
    """
    Fetch student record by ID from MongoDB.
    
    Args:
        student_id: The student ID (UUID format) to look up
        
    Returns:
        Formatted string with student information or error message
    """
    print(f"DEBUG: fetch_student_record called with student_id: {student_id}")
    
    # Validate format first
    if not validate_student_id_format(student_id):
        print(f"DEBUG: Invalid student ID format: {student_id}")
        return f"Invalid student ID format: {student_id}. Expected format: Valid UUID (e.g., 1ef47dda-5884-422b-b84b-2ee3d119b0c7)"
    
    print(f"DEBUG: Student ID format is valid")
    
    # Fetch the record
    print(f"DEBUG: Calling get_student_by_id...")
    student_record = get_student_by_id(student_id)
    print(f"DEBUG: get_student_by_id returned: {student_record}")
    
    if student_record is None:
        print(f"DEBUG: Student record is None, getting available IDs...")
        available_ids = get_all_student_ids()
        print(f"DEBUG: Available IDs: {available_ids}")
        return f"Student ID {student_id} not found. Available student IDs: {', '.join(available_ids[:5])}{'...' if len(available_ids) > 5 else ''}"
    
    print(f"DEBUG: Student record found, formatting...")
    
    # Format the record nicely
    formatted_record = f"""
    Student Record Found:
    ====================
    Student ID: {student_record['student_id']}
    Name: {student_record['name']}
    First Name: {student_record.get('first_name', 'N/A')}
    Last Name: {student_record.get('last_name', 'N/A')}
    Email: {student_record.get('email', 'N/A')}
    Phone: {student_record.get('phone', 'N/A')}
    Birthdate: {student_record.get('birthdate', 'N/A')}
    Gender: {student_record.get('gender', 'N/A')}
    Applying Grade: {student_record.get('applying_grade', 'N/A')}
    Has Birth Certificate: {'Yes' if student_record.get('documents', {}).get('birth_certificate') else 'No'}
    ====================
    """
    print(f"DEBUG: Returning formatted record")
    return formatted_record

@function_tool
async def process_birth_certificate(
    context: RunContextWrapper[EnhancedValidationContext], 
    student_id: str,
    use_stu_format: bool = False
) -> str:
    """
    Process a birth certificate image and compare with student data.
    Checks local files first (in spike/docs/), then falls back to S3 if not found.
    
    Args:
        student_id: The student ID (UUID or STU### format) to compare against
        use_stu_format: If True, will look for STU### format files in docs folder
        
    Returns:
        Comparison results and anomaly report
    """
    # For testing with local files, we can accept STU### format
    if use_stu_format or student_id.startswith("STU"):
        # Use the STU format directly for local file lookup
        birth_cert_source = f"docs/{student_id}.png"
    else:
        # Validate UUID format
        if not validate_student_id_format(student_id):
            return f"Invalid student ID format: {student_id}. Expected format: Valid UUID or STU###"
        
        # Get birth certificate source (local file or S3 URL)
        birth_cert_source = get_birth_certificate_source(student_id, prefer_local=True)
        
        if not birth_cert_source:
            # If no source found, check if we can find a local STU file
            # This is a temporary workaround for testing
            birth_cert_source = "STU001"  # Default to STU001 for testing
    
    try:
        # Extract data from birth certificate using GPT Vision
        extracted_data = extract_data_from_birth_certificate(birth_cert_source, prefer_local=True)
        
        # For comparison, we need the actual MongoDB student ID (UUID)
        # If we used STU format, try to find the corresponding UUID
        comparison_student_id = student_id
        if student_id.startswith("STU"):
            # For testing, we'll use the first available student
            available_students = get_all_student_ids()
            if available_students:
                comparison_student_id = available_students[0].split(' ')[0]  # Extract UUID
            else:
                return "No students found in MongoDB for comparison"
        
        # Compare with MongoDB data
        comparison_result = compare_student_data(comparison_student_id, extracted_data)
        
        if comparison_result["status"] == "error":
            return comparison_result["message"]
        
        # Store results in context for potential updates
        context.context.last_student_id = comparison_student_id
        context.context.document_data = extracted_data
        
        # Format the comparison report
        report = f"""
    Document Processing Results:
    ===========================

    Student ID: {comparison_student_id}
    Birth Certificate Source: {birth_cert_source}
    Source Type: {'Local File' if not birth_cert_source.startswith('http') else 'S3 URL'}

    EXTRACTED FROM BIRTH CERTIFICATE:
    {json.dumps(extracted_data, indent=2)}

    MONGODB RECORD:
    Name: {comparison_result['mongodb_record'].get('name', 'N/A')}
    First Name: {comparison_result['mongodb_record'].get('first_name', 'N/A')}
    Last Name: {comparison_result['mongodb_record'].get('last_name', 'N/A')}
    Birthdate: {comparison_result['mongodb_record'].get('birthdate', 'N/A')}

    COMPARISON RESULTS:
    """
        
        if comparison_result["matches"]:
            report += "\n✅ MATCHES:\n"
            for match in comparison_result["matches"]:
                report += f"   • {match['field']}: {match['value']}\n"
        
        if comparison_result["anomalies"]:
            report += f"\n⚠️  ANOMALIES DETECTED ({len(comparison_result['anomalies'])}):\n"
            context.context.pending_updates = {}
            
            for anomaly in comparison_result["anomalies"]:
                report += f"   • {anomaly['field']}:\n"
                report += f"     MongoDB: '{anomaly['mongodb_value']}'\n"
                report += f"     Certificate: '{anomaly['certificate_value']}'\n"
                
                # Store potential update
                context.context.pending_updates[anomaly['field']] = anomaly['certificate_value']
            
            report += "\n📝 Would you like me to update MongoDB with the certificate data? Say 'yes' to approve updates."
        else:
            report += "\n✅ No anomalies detected! MongoDB data matches the birth certificate."
        
        if comparison_result["additional_info"]:
            report += "\n📄 ADDITIONAL CERTIFICATE INFO:\n"
            for key, value in comparison_result["additional_info"].items():
                report += f"   • {key}: {value}\n"
        
        return report
        
    except Exception as e:
        return f"Error processing birth certificate: {e}"

@function_tool
async def approve_mongodb_updates(context: RunContextWrapper[EnhancedValidationContext]) -> str:
    """
    Apply the pending updates to MongoDB after approval.
    
    Returns:
        Result of the update operation
    """
    if not context.context.pending_updates or not context.context.last_student_id:
        return "No pending updates to apply. Please process a birth certificate first."
    
    try:
        # Apply the updates
        import pdb; pdb.set_trace()
        result = update_mongodb_record(context.context.last_student_id, context.context.pending_updates)
        
        if result["status"] == "success":
            # Clear pending updates
            updates_made = context.context.pending_updates.copy()
            context.context.pending_updates = None
            
            report = f"""
    ✅ MONGODB UPDATE SUCCESSFUL!

    Student ID: {context.context.last_student_id}
    Updated Fields:
    """
            for field, new_value in updates_made.items():
                report += f"   • {field}: {new_value}\n"
            
            report += f"\n{result['message']}"
            return report
        else:
            return f"❌ Update failed: {result['message']}"
            
    except Exception as e:
        return f"❌ Error updating MongoDB: {e}"

@function_tool
async def list_available_students() -> str:
    """
    List all available student IDs in MongoDB.
    
    Returns:
        Formatted string with all available student IDs
    """
    student_ids = get_all_student_ids()
    if not student_ids:
        return "No student records found in MongoDB."
    
    # Format the list nicely
    report = "Available Students in MongoDB:\n"
    report += "==============================\n"
    for idx, student_info in enumerate(student_ids[:20], 1):  # Limit to first 20
        report += f"{idx}. {student_info}\n"
    
    if len(student_ids) > 20:
        report += f"\n... and {len(student_ids) - 20} more students"
    
    return report

@function_tool
async def process_birth_certificate_by_url(
    context: RunContextWrapper[EnhancedValidationContext], 
    student_id: str,
    image_url: str
) -> str:
    """
    Process a birth certificate from a custom URL or local path.
    
    Args:
        student_id: The student ID to compare against
        image_url: Direct URL or local path to the birth certificate image
        
    Returns:
        Comparison results and anomaly report
    """
    # Validate inputs
    if not validate_student_id_format(student_id) and not student_id.startswith("STU"):
        return f"Invalid student ID format: {student_id}. Expected format: Valid UUID or STU###"
    
    if not validate_image_file(image_url):
        return f"Invalid or inaccessible image: {image_url}"
    
    try:
        # Extract data from birth certificate using GPT Vision
        extracted_data = extract_data_from_birth_certificate(image_url)
        
        # For comparison, we need the actual MongoDB student ID (UUID)
        comparison_student_id = student_id
        if student_id.startswith("STU"):
            # For testing, we'll use the first available student
            available_students = get_all_student_ids()
            if available_students:
                comparison_student_id = available_students[0].split(' ')[0]  # Extract UUID
            else:
                return "No students found in MongoDB for comparison"
        
        # Compare with MongoDB data
        comparison_result = compare_student_data(comparison_student_id, extracted_data)
        
        if comparison_result["status"] == "error":
            return comparison_result["message"]
        
        # Store results in context for potential updates
        context.context.last_student_id = comparison_student_id
        context.context.document_data = extracted_data
        
        # Format the comparison report (similar to process_birth_certificate)
        report = f"""
    Document Processing Results:
    ===========================

    Student ID: {comparison_student_id}
    Custom Image Path: {image_url}

    EXTRACTED FROM BIRTH CERTIFICATE:
    {json.dumps(extracted_data, indent=2)}

    MONGODB RECORD:
    Name: {comparison_result['mongodb_record'].get('name', 'N/A')}
    First Name: {comparison_result['mongodb_record'].get('first_name', 'N/A')}
    Last Name: {comparison_result['mongodb_record'].get('last_name', 'N/A')}
    Birthdate: {comparison_result['mongodb_record'].get('birthdate', 'N/A')}

    COMPARISON RESULTS:
    """
        
        if comparison_result["matches"]:
            report += "\n✅ MATCHES:\n"
            for match in comparison_result["matches"]:
                report += f"   • {match['field']}: {match['value']}\n"
        
        if comparison_result["anomalies"]:
            report += f"\n⚠️  ANOMALIES DETECTED ({len(comparison_result['anomalies'])}):\n"
            context.context.pending_updates = {}
            
            for anomaly in comparison_result["anomalies"]:
                report += f"   • {anomaly['field']}:\n"
                report += f"     MongoDB: '{anomaly['mongodb_value']}'\n"
                report += f"     Certificate: '{anomaly['certificate_value']}'\n"
                
                # Store potential update
                context.context.pending_updates[anomaly['field']] = anomaly['certificate_value']
            
            report += "\n📝 Would you like me to update MongoDB with the certificate data? Say 'yes' to approve updates."
        else:
            report += "\n✅ No anomalies detected! MongoDB data matches the birth certificate."
        
        if comparison_result["additional_info"]:
            report += "\n📄 ADDITIONAL CERTIFICATE INFO:\n"
            for key, value in comparison_result["additional_info"].items():
                report += f"   • {key}: {value}\n"
        
        return report
        
    except Exception as e:
        return f"Error processing birth certificate: {e}"

# Create the enhanced validation agent
enhanced_validation_agent = Agent[EnhancedValidationContext](
    name="Enhanced Student Validation Agent (MongoDB + Local Files)",
    instructions="""
    You are an enhanced student validation agent with MongoDB integration and local file support. Your role is to:
    
    1. **Student Record Lookup**: Fetch student records from MongoDB by UUID
    2. **Document Processing**: Process birth certificate images from local files (spike/docs/) or S3
    3. **Data Validation**: Compare extracted document data with MongoDB records to detect anomalies
    4. **MongoDB Updates**: Offer to update MongoDB records when discrepancies are found
    
    ## Important Notes:
    - Student IDs in MongoDB are UUIDs (e.g., 1ef47dda-5884-422b-b84b-2ee3d119b0c7)
    - Birth certificates can be in local spike/docs/ folder (e.g., STU001.png) or S3
    - The system checks local files first, then falls back to S3
    
    ## Workflow:
    
    **For basic student lookup:**
    - When user provides a UUID (e.g., "966ec437-a9da-4259-9c55-4f6bfdc7e85b"), ALWAYS use the fetch_student_record tool
    - When user asks to "look up student" or "fetch student", use fetch_student_record tool
    - When user asks to "list students", use list_available_students tool
    
    **For document validation with local files:**
    1. Use process_birth_certificate tool with either:
       - A UUID (will check for local files first, then S3)
    2. Review the comparison results and anomalies
    3. If anomalies are found, ask user for approval to update MongoDB
    4. If approved, use approve_mongodb_updates tool to apply changes
    
    **For custom paths:**
    - Use process_birth_certificate_by_url with any custom path or URL
    
    ## IMPORTANT: When to use tools
    - If user provides a UUID string, IMMEDIATELY use fetch_student_record tool
    - If user asks to list students, use list_available_students tool
    - If user mentions birth certificate processing, use process_birth_certificate tool
    - Do NOT try to handle UUID lookups conversationally - always use the appropriate tool
    
    ## Examples:
    - User types "966ec437-a9da-4259-9c55-4f6bfdc7e85b" → Use fetch_student_record tool
    - User types "look up student 966ec437-a9da-4259-9c55-4f6bfdc7e85b" → Use fetch_student_record tool
    - User types "list students" → Use list_available_students tool
    - User types "Process birth certificate STU001" → Use process_birth_certificate tool
    
    ## Guidelines:
    - Always validate ID format before processing
    - Be thorough in explaining anomalies and what will be updated
    - Ask for explicit user approval before making any MongoDB changes
    - Provide clear summaries of what was updated
    - Handle errors gracefully and provide helpful guidance
    
    Be conversational, professional, and thorough in your responses.
    """,
    tools=[fetch_student_record, process_birth_certificate, approve_mongodb_updates, list_available_students, process_birth_certificate_by_url]
)

async def main():
    """Main function to run the enhanced validation agent."""
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running the agent:")
        print("For Windows PowerShell: $env:OPENAI_API_KEY=\"your_api_key_here\"")
        print("For Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        return
    
    # Check if MongoDB URI is set
    if not os.getenv("MONGODB_URI"):
        print("Warning: MONGODB_URI environment variable not set.")
        print("Please set it in your .env file or environment.")
        return
    
    print("Enhanced Student Validation Agent (MongoDB + Local Files) Initialized")
    print("==================================================================")
    print("This agent can:")
    print("• Look up student records from MongoDB by UUID")
    print("• Process birth certificate images from local files or S3")
    print("• Compare document data with MongoDB records")
    print("• Detect and fix data anomalies with your approval")
    print()
    print("Local Files Support:")
    print("• Birth certificates in spike/docs/ folder (e.g., STU001.png)")
    print("• Direct path support (e.g., E:/path/to/certificate.png)")
    print()
    print("Examples:")
    print('• "Look up student 1ef47dda-5884-422b-b84b-2ee3d119b0c7"')
    print('• "Process birth certificate STU001" (uses local file)')
    print('• "Process birth certificate for student 1ef47dda-5884-422b-b84b-2ee3d119b0c7"')
    print('• "List available students"')
    print()
    print("Type 'quit' to exit.")
    print()
    
    context = EnhancedValidationContext()
    input_items = []
    
    while True:
        try:
            user_input = input("Stakeholder: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Thank you for using the Enhanced Student Validation Agent!")
                break
            
            if not user_input:
                continue
            
            # Add user input to conversation
            input_items.append({"content": user_input, "role": "user"})
            
            # Run the agent
            result = await Runner.run(enhanced_validation_agent, input_items, context=context)
            
            # Get the final response - using the same pattern as the airline example
            from agents import MessageOutputItem, ToolCallItem, ToolCallOutputItem, ItemHelpers
            
            for new_item in result.new_items:
                agent_name = new_item.agent.name
                if isinstance(new_item, MessageOutputItem):
                    print(f"Agent: {ItemHelpers.text_message_output(new_item)}")
                elif isinstance(new_item, ToolCallItem):
                    print(f"{agent_name}: Processing...")
                elif isinstance(new_item, ToolCallOutputItem):
                    # Don't print raw tool output as it will be processed by the agent
                    pass
                else:
                    print(f"{agent_name}: {new_item.__class__.__name__}")
            
            # Update input items for next iteration
            input_items = result.to_input_list()
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 