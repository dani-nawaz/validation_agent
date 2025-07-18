import os
import asyncio
import json
from pydantic import BaseModel
from database import get_enrollement_data_from_db
from agents import Agent, Runner, function_tool, RunContextWrapper
from student_tools import get_student_by_id, validate_student_id_format, get_all_student_ids
from document_tools import (
    extract_data_from_birth_certificate,
    compare_student_data,
    update_csv_record,
    validate_image_file
)

# Enhanced context for the validation agent
class EnhancedValidationContext(BaseModel):
    last_student_id: str | None = None
    pending_updates: dict | None = None
    document_data: dict | None = None

# Enhanced tool functions using the proper decorator
@function_tool
async def fetch_student_record(student_id: str) -> str:
    """
    Fetch student record by ID from the CSV database.
    
    Args:
        student_id: The student ID to look up (format: STU###)
        
    Returns:
        Formatted string with student information or error message
    """
    enrollmentForm_data = get_enrollement_data_from_db()
    print(enrollmentForm_data)
    # Validate format first
    if not validate_student_id_format(student_id):
        return f"Invalid student ID format: {student_id}. Expected format: STU### (e.g., STU001)"
    
    # Fetch the record
    student_record = get_student_by_id(student_id)
    
    if student_record is None:
        available_ids = get_all_student_ids()
        return f"Student ID {student_id} not found. Available student IDs: {', '.join(available_ids[:5])}{'...' if len(available_ids) > 5 else ''}"
    
    # Format the record nicely
    formatted_record = f"""
Student Record Found:
====================
Student ID: {student_record['student_id']}
Name: {student_record['name']}
Email: {student_record['email']}
Major: {student_record['major']}
GPA: {student_record['gpa']}
Enrollment Year: {student_record['enrollment_year']}
====================
"""
    return formatted_record

@function_tool
async def process_birth_certificate(
    context: RunContextWrapper[EnhancedValidationContext], 
    student_id: str
) -> str:
    """
    Process a birth certificate image and compare with student CSV data.
    Automatically looks for the document at docs/<student_id>.png
    
    Args:
        student_id: The student ID to compare against
        
    Returns:
        Comparison results and anomaly report
    """
    # Validate inputs
    if not validate_student_id_format(student_id):
        return f"Invalid student ID format: {student_id}. Expected format: STU### (e.g., STU001)"
    
    # Construct image path based on student ID
    image_path = f"docs/{student_id}.png"
    
    if not validate_image_file(image_path):
        return f"Birth certificate not found: {image_path}. Please ensure the document exists in the docs folder."
    
    try:
        # Extract data from birth certificate using GPT Vision
        extracted_data = extract_data_from_birth_certificate(image_path)
        
        # Compare with CSV data
        comparison_result = compare_student_data(student_id, extracted_data)
        
        if comparison_result["status"] == "error":
            return comparison_result["message"]
        
        # Store results in context for potential updates
        context.context.last_student_id = student_id
        context.context.document_data = extracted_data
        
        # Format the comparison report
        report = f"""
Document Processing Results:
===========================

Student ID: {student_id}

EXTRACTED FROM BIRTH CERTIFICATE:
{json.dumps(extracted_data, indent=2)}

CSV RECORD:
{json.dumps(comparison_result['csv_record'], indent=2)}

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
                report += f"     CSV: '{anomaly['csv_value']}'\n"
                report += f"     Certificate: '{anomaly['certificate_value']}'\n"
                
                # Store potential update
                context.context.pending_updates[anomaly['field']] = anomaly['certificate_value']
            
            report += "\n📝 Would you like me to update the CSV with the certificate data? Say 'yes' to approve updates."
        else:
            report += "\n✅ No anomalies detected! CSV data matches the birth certificate."
        
        if comparison_result["additional_info"]:
            report += "\n📄 ADDITIONAL CERTIFICATE INFO:\n"
            for key, value in comparison_result["additional_info"].items():
                report += f"   • {key}: {value}\n"
        
        return report
        
    except Exception as e:
        return f"Error processing birth certificate: {e}"

@function_tool
async def approve_csv_updates(context: RunContextWrapper[EnhancedValidationContext]) -> str:
    """
    Apply the pending updates to the CSV file after approval.
    
    Returns:
        Result of the update operation
    """
    if not context.context.pending_updates or not context.context.last_student_id:
        return "No pending updates to apply. Please process a birth certificate first."
    
    try:
        # Apply the updates
        result = update_csv_record(context.context.last_student_id, context.context.pending_updates)
        
        if result["status"] == "success":
            # Clear pending updates
            updates_made = context.context.pending_updates.copy()
            context.context.pending_updates = None
            
            report = f"""
✅ CSV UPDATE SUCCESSFUL!

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
        return f"❌ Error updating CSV: {e}"

@function_tool
async def list_available_students() -> str:
    """
    List all available student IDs in the database.
    
    Returns:
        Formatted string with all available student IDs
    """
    student_ids = get_all_student_ids()
    if not student_ids:
        return "No student records found in the database."
    
    return f"Available Student IDs: {', '.join(student_ids)}"

@function_tool
async def list_available_documents() -> str:
    """
    List all available birth certificate documents in the docs folder.
    
    Returns:
        Formatted string with available documents and their corresponding student IDs
    """
    docs_folder = "docs"
    if not os.path.exists(docs_folder):
        return "Docs folder not found. Please create a 'docs' folder with birth certificate PNG files."
    
    try:
        files = os.listdir(docs_folder)
        png_files = [f for f in files if f.endswith('.png')]
        
        if not png_files:
            return "No PNG documents found in the docs folder."
        
        # Extract student IDs from filenames
        student_docs = []
        for filename in png_files:
            student_id = filename.replace('.png', '')
            if validate_student_id_format(student_id):
                student_docs.append(student_id)
        
        if not student_docs:
            return f"Found {len(png_files)} PNG files in docs folder, but none follow the STU### naming convention."
        
        return f"Available birth certificates: {', '.join(student_docs)} (Total: {len(student_docs)} documents)"
        
    except Exception as e:
        return f"Error reading docs folder: {e}"

# Create the enhanced validation agent
enhanced_validation_agent = Agent[EnhancedValidationContext](
    name="Enhanced Student Validation Agent",
    instructions="""
    You are an enhanced student validation agent with document processing capabilities. Your role is to:
    
    1. **Student Record Lookup**: Fetch student records from CSV database by ID
    2. **Document Processing**: Process birth certificate images using GPT Vision to extract data
    3. **Data Validation**: Compare extracted document data with CSV records to detect anomalies
    4. **CSV Updates**: Offer to update CSV records when discrepancies are found
    
    ## Workflow:
    
    **For basic student lookup:**
    - Use fetch_student_record tool with student ID
    
    **For document validation:**
    1. Use process_birth_certificate tool with just the student ID (automatically finds docs/<student_id>.png)
    2. Review the comparison results and anomalies
    3. If anomalies are found, ask user for approval to update CSV
    4. If approved, use approve_csv_updates tool to apply changes
    
    ## Guidelines:
    - Always validate student ID format (STU###)
    - Be thorough in explaining anomalies and what will be updated
    - Ask for explicit user approval before making any CSV changes
    - Provide clear summaries of what was updated
    - Handle errors gracefully and provide helpful guidance
    
    Be conversational, professional, and thorough in your responses.
    """,
    tools=[fetch_student_record, process_birth_certificate, approve_csv_updates, list_available_students, list_available_documents]
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
    
    print("Enhanced Student Validation Agent Initialized")
    print("============================================")
    print("This agent can:")
    print("• Look up student records from CSV database")
    print("• Process birth certificate images using GPT Vision")
    print("• Compare document data with CSV records")
    print("• Detect and fix data anomalies with your approval")
    print()
    print("Examples:")
    print('• "Look up student STU001"')
    print('• "Process birth certificate for student STU001"')
    print('• "Validate STU001 against their birth certificate"')
    print('• "What students are available?"')
    print('• "What documents are available?"')
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