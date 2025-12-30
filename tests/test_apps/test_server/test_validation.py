"""Tests for the validation utilities."""
import sys

sys.path.append(".")

import pytest

from src.apps.server.validation import (
    ValidationError,
    validate_code,
    validate_student_id,
    validate_session_id,
    validate_timeout,
    validate_test_cases,
    sanitize_output,
    validate_command
)


class TestValidateCode:
    """Tests for validate_code function."""
    
    def test_valid_code(self):
        """Test validation of valid code."""
        code = "print('Hello World')"
        result = validate_code(code)
        assert result == code
    
    def test_empty_code_raises_error(self):
        """Test that empty code raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_code("")
        assert exc_info.value.field == "code"
        assert "empty" in exc_info.value.message.lower()
    
    def test_code_exceeds_max_length(self):
        """Test that code exceeding max length raises error."""
        long_code = "x" * 101
        with pytest.raises(ValidationError) as exc_info:
            validate_code(long_code, max_length=100)
        assert "exceeds maximum length" in exc_info.value.message


class TestValidateStudentId:
    """Tests for validate_student_id function."""
    
    def test_valid_student_id(self):
        """Test validation of valid student ID."""
        result = validate_student_id("student_123")
        assert result == "student_123"
    
    def test_valid_student_id_with_dots(self):
        """Test validation of student ID with dots."""
        result = validate_student_id("john.doe")
        assert result == "john.doe"
    
    def test_empty_student_id_raises_error(self):
        """Test that empty student ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_student_id("")
        assert exc_info.value.field == "student_id"
    
    def test_student_id_with_invalid_chars(self):
        """Test that student ID with invalid characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_student_id("student@123")
        assert "invalid characters" in exc_info.value.message.lower()


class TestValidateSessionId:
    """Tests for validate_session_id function."""
    
    def test_valid_session_id(self):
        """Test validation of valid session ID."""
        result = validate_session_id("abc123")
        assert result == "abc123"
    
    def test_session_id_with_hyphens(self):
        """Test validation of session ID with hyphens."""
        result = validate_session_id("session-abc-123")
        assert result == "session-abc-123"
    
    def test_empty_session_id_raises_error(self):
        """Test that empty session ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_session_id("")
        assert exc_info.value.field == "session_id"


class TestValidateTimeout:
    """Tests for validate_timeout function."""
    
    def test_valid_timeout(self):
        """Test validation of valid timeout."""
        result = validate_timeout(30)
        assert result == 30
    
    def test_timeout_below_minimum(self):
        """Test that timeout below minimum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_timeout(0)
        assert "at least" in exc_info.value.message.lower()
    
    def test_timeout_above_maximum(self):
        """Test that timeout above maximum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_timeout(500)
        assert "cannot exceed" in exc_info.value.message.lower()


class TestValidateTestCases:
    """Tests for validate_test_cases function."""
    
    def test_valid_test_cases(self):
        """Test validation of valid test cases."""
        cases = [{"input": [], "output": []}]
        result = validate_test_cases(cases)
        assert result == cases
    
    def test_empty_test_cases_raises_error(self):
        """Test that empty test cases raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_test_cases([])
        assert "at least one" in exc_info.value.message.lower()
    
    def test_too_many_test_cases(self):
        """Test that too many test cases raises error."""
        cases = [{"input": [], "output": []} for _ in range(10)]
        with pytest.raises(ValidationError) as exc_info:
            validate_test_cases(cases, max_cases=5)
        assert "maximum" in exc_info.value.message.lower()


class TestSanitizeOutput:
    """Tests for sanitize_output function."""
    
    def test_normal_output(self):
        """Test sanitization of normal output."""
        result = sanitize_output("Hello World")
        assert result == "Hello World"
    
    def test_empty_output(self):
        """Test sanitization of empty output."""
        result = sanitize_output("")
        assert result == ""
    
    def test_null_output(self):
        """Test sanitization of None output."""
        result = sanitize_output(None)
        assert result == ""
    
    def test_output_with_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_output("Hello\x00World")
        assert result == "HelloWorld"
    
    def test_long_output_truncated(self):
        """Test that long output is truncated."""
        long_output = "x" * 60000
        result = sanitize_output(long_output)
        assert len(result) < 60000
        assert "truncated" in result


class TestValidateCommand:
    """Tests for validate_command function."""
    
    def test_valid_python_command(self):
        """Test validation of python command."""
        result = validate_command("python3")
        assert result == "python3"
    
    def test_valid_node_command(self):
        """Test validation of node command."""
        result = validate_command("node")
        assert result == "node"
    
    def test_empty_command_raises_error(self):
        """Test that empty command raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_command("")
        assert exc_info.value.field == "command"
