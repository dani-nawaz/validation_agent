# Student Validation Agent

A simple validation agent built with the OpenAI Agents SDK that helps stakeholders look up student records from a CSV database.

## Features

- **Interactive Student ID Validation**: Asks stakeholders for student IDs and validates format
- **CSV Record Fetching**: Retrieves student information from a CSV database
- **Format Validation**: Ensures student IDs follow the expected format (STU + 3 digits)
- **Error Handling**: Provides helpful feedback for invalid or missing student records
- **Available Students Listing**: Can show all available student IDs

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API Key**:
   
   **Linux/Mac (bash):**
   ```bash
   export OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **Windows (PowerShell):**
   ```powershell
   $env:OPENAI_API_KEY="your_openai_api_key_here"
   ```

3. **Run the Agent**:
   ```bash
   python validation_agent.py
   ```

## Usage

The agent will start an interactive session where you can:

- Provide student IDs directly: `"Look up student STU001"`
- Ask for available students: `"What students are available?"`
- Request help: `"How do I find a student?"`

### Example Interactions

```
Stakeholder: I need to look up student STU001
Agent: [Fetches and displays student record]

Stakeholder: What students are available?
Agent: Available Student IDs: STU001, STU002, STU003, STU004, STU005...

Stakeholder: Look up student ABC123
Agent: Invalid student ID format: ABC123. Expected format: STU### (e.g., STU001)
```

## Sample Data

The system comes with sample student data in `students.csv` including:
- Student ID
- Name
- Email
- Major
- GPA
- Enrollment Year

## Architecture

- **validation_agent.py**: Main agent implementation using OpenAI Agents SDK
- **student_tools.py**: Utility functions for CSV operations and validation
- **students.csv**: Sample student database
- **requirements.txt**: Python dependencies

## Customization

You can easily customize the agent by:
- Modifying the CSV structure in `students.csv`
- Updating validation rules in `student_tools.py`
- Changing agent instructions in `validation_agent.py`
- Adding new tools for additional functionality 