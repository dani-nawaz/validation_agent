import os
from agents import Agent, Runner
from student_tools import get_student_by_id, validate_student_id_format, get_all_student_ids

def main():
    """Simple test to see if the basic agent works."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create a simple agent without custom tools first
    agent = Agent(
        name="Test Agent", 
        instructions="You are a helpful assistant."
    )
    
    try:
        result = Runner.run_sync(agent, "Say hello!")
        print("Agent Response:", result.final_output)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 