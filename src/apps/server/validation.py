"""Validation utilities for the Testio server."""
import sys
import re
from typing import List, Optional, Any

sys.path.append(".")


class ValidationError(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_code(code: str, max_length: int = 100000) -> str:
    """
    Validate and sanitize code input.
    
    :param code: The code to validate
    :param max_length: Maximum allowed length
    :return: Validated code
    :raises ValidationError: If validation fails
    """
    if not code:
        raise ValidationError("Code cannot be empty", "code")
    
    if len(code) > max_length:
        raise ValidationError(
            f"Code exceeds maximum length of {max_length} characters",
            "code"
        )
    
    return code


def validate_student_id(student_id: str) -> str:
    """
    Validate a student ID.
    
    :param student_id: The student ID to validate
    :return: Validated student ID
    :raises ValidationError: If validation fails
    """
    if not student_id:
        raise ValidationError("Student ID cannot be empty", "student_id")
    
    if len(student_id) > 100:
        raise ValidationError("Student ID is too long", "student_id")
    
    # Allow alphanumeric, underscores, hyphens, and dots
    if not re.match(r'^[\w.\-]+$', student_id):
        raise ValidationError(
            "Student ID contains invalid characters",
            "student_id"
        )
    
    return student_id.strip()


def validate_session_id(session_id: str) -> str:
    """
    Validate a session ID.
    
    :param session_id: The session ID to validate
    :return: Validated session ID
    :raises ValidationError: If validation fails
    """
    if not session_id:
        raise ValidationError("Session ID cannot be empty", "session_id")
    
    if len(session_id) > 50:
        raise ValidationError("Session ID is too long", "session_id")
    
    # Allow alphanumeric and hyphens only
    if not re.match(r'^[\w\-]+$', session_id):
        raise ValidationError(
            "Session ID contains invalid characters",
            "session_id"
        )
    
    return session_id.strip()


def validate_timeout(timeout: int, min_timeout: int = 1, max_timeout: int = 300) -> int:
    """
    Validate a timeout value.
    
    :param timeout: The timeout value to validate
    :param min_timeout: Minimum allowed timeout
    :param max_timeout: Maximum allowed timeout
    :return: Validated timeout
    :raises ValidationError: If validation fails
    """
    if timeout < min_timeout:
        raise ValidationError(
            f"Timeout must be at least {min_timeout} seconds",
            "timeout"
        )
    
    if timeout > max_timeout:
        raise ValidationError(
            f"Timeout cannot exceed {max_timeout} seconds",
            "timeout"
        )
    
    return timeout


def validate_test_cases(test_cases: List[Any], max_cases: int = 100) -> List[Any]:
    """
    Validate test cases list.
    
    :param test_cases: List of test cases to validate
    :param max_cases: Maximum number of test cases allowed
    :return: Validated test cases
    :raises ValidationError: If validation fails
    """
    if not test_cases:
        raise ValidationError("At least one test case is required", "tests")
    
    if len(test_cases) > max_cases:
        raise ValidationError(
            f"Maximum {max_cases} test cases allowed",
            "tests"
        )
    
    return test_cases


def sanitize_output(output: str) -> str:
    """
    Sanitize output strings for safe display.
    
    :param output: The output to sanitize
    :return: Sanitized output
    """
    if not output:
        return ""
    
    # Remove null bytes
    output = output.replace('\x00', '')
    
    # Limit output length to prevent memory issues
    max_length = 50000
    if len(output) > max_length:
        output = output[:max_length] + "\n... (output truncated)"
    
    return output


def validate_command(command: str) -> str:
    """
    Validate a command string.
    
    :param command: The command to validate
    :return: Validated command
    :raises ValidationError: If validation fails
    """
    if not command:
        raise ValidationError("Command cannot be empty", "command")
    
    # Basic command validation - allow common interpreters
    allowed_commands = [
        'python', 'python3', 'python2',
        'node', 'nodejs',
        'ruby', 'perl',
        'java', 'javac',
        'go', 'go run',
        'gcc', 'g++', 'clang',
        'bash', 'sh'
    ]
    
    # Extract base command
    base_command = command.split()[0].lower()
    
    # Check if it's a known safe command or a path to an executable
    is_safe = (
        base_command in allowed_commands or
        base_command.startswith('./')  # Local executable
    )
    
    if not is_safe:
        # Log warning but don't block - allow for flexibility
        pass
    
    return command
