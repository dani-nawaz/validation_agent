import os
from agents import Agent, Runner
from student_tools import get_student_by_id, validate_student_id_format, get_all_student_ids
from typing import Dict, Any, Optional



class StudentValidationAgent:
    """
    A validation agent that helps stakeholders look up student records.
    """
    
    def __init__(self):
        self.agent = Agent(
            name="Student Validation Agent",
            instructions="""
            You are a helpful student validation agent. Your role is to:
            
            1. Ask stakeholders for student IDs when they want to look up student records
            2. Validate the student ID format (should be STU followed by 3 digits, e.g., STU001)
            3. Fetch and display student records from the database
            4. Provide helpful guidance if student IDs are not found or invalid
            
            When a stakeholder provides a student ID:
            - First validate the format
            - Then fetch the record using the fetch_student_record tool
            - Present the information in a clear, professional manner
            
            If no student ID is provided initially, politely ask for one.
            If multiple student IDs are mentioned, process them one by one.
            
            Be conversational and helpful throughout the interaction.
            """,
            tools=[self.fetch_student_record, self.list_available_students]
        )
    
    def fetch_student_record(self, student_id: str) -> str:
        """
        Fetch student record by ID from the CSV database.
        
        Args:
            student_id (str): The student ID to look up (format: STU###)
            
        Returns:
            str: Formatted string with student information or error message
        """
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

    def list_available_students(self) -> str:
        """
        List all available student IDs in the database.
        
        Returns:
            str: Formatted string with all available student IDs
        """
        student_ids = get_all_student_ids()
        if not student_ids:
            return "No student records found in the database."
        
        return f"Available Student IDs: {', '.join(student_ids)}"
    
    def run(self, message: str) -> str:
        """
        Run the validation agent with a message.
        
        Args:
            message: The input message from the stakeholder
            
        Returns:
            The agent's response
        """
        try:
            result = Runner.run_sync(self.agent, message)
            return result.final_output
        except Exception as e:
            return f"Error running validation agent: {e}"

def main():
    """
    Main function to demonstrate the validation agent.
    """
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running the agent:")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    print("Student Validation Agent Initialized")
    print("=====================================")
    print("This agent helps stakeholders look up student records.")
    print("You can provide student IDs or ask for available students.")
    print("Type 'quit' to exit.")
    print()
    
    agent = StudentValidationAgent()
    
    while True:
        try:
            user_input = input("Stakeholder: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Thank you for using the Student Validation Agent!")
                break
            
            if not user_input:
                continue
            
            print("\nAgent: ", end="")
            response = agent.run(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 