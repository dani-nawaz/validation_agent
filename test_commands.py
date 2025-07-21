#!/usr/bin/env python3
"""
Common test commands for the Student Validation API.
"""

import subprocess
import sys


def run_command(cmd: list):
    """Run a command and return success status."""
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    """Main function to handle different test commands."""
    if len(sys.argv) < 2:
        print("Usage: python test_commands.py <command>")
        print("\nAvailable commands:")
        print("  all          - Run all tests")
        print("  unit         - Run only unit tests")
        print("  integration  - Run only integration tests")
        print("  api          - Run only API tests")
        print("  fast         - Run fast tests (exclude slow tests)")
        print("  coverage     - Run tests with coverage report")
        print("  verbose      - Run tests with verbose output")
        print("  help         - Show pytest help")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if command == "all":
        cmd = base_cmd + ["-v", "tests/"]
    elif command == "unit":
        cmd = base_cmd + ["-v", "-m", "unit", "tests/"]
    elif command == "integration":
        cmd = base_cmd + ["-v", "-m", "integration", "tests/"]
    elif command == "api":
        cmd = base_cmd + ["-v", "-m", "api", "tests/"]
    elif command == "fast":
        cmd = base_cmd + ["-v", "-m", "not slow", "tests/"]
    elif command == "coverage":
        cmd = base_cmd + ["--cov=api", "--cov-report=html", "--cov-report=term", "tests/"]
    elif command == "verbose":
        cmd = base_cmd + ["-v", "-s", "--tb=long", "tests/"]
    elif command == "help":
        cmd = base_cmd + ["--help"]
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    success = run_command(cmd)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 