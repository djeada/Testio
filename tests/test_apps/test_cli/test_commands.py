"""
Tests for the CLI commands module.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.append(".")

from src.apps.cli.commands import validate, batch, export, generate, init


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_valid_config(self):
        """Test that a valid config passes validation."""
        config = {
            "command": "python3",
            "path": "test.py",
            "tests": [
                {
                    "input": ["test"],
                    "output": ["test"],
                    "timeout": 10
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            result = validate.validate_config(temp_path)
            assert result["valid"] is True
            assert len(result["errors"]) == 0
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_missing_command(self):
        """Test that config without command fails validation."""
        config = {
            "path": "test.py",
            "tests": [
                {
                    "input": ["test"],
                    "output": ["test"],
                    "timeout": 10
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            result = validate.validate_config(temp_path)
            assert result["valid"] is False
            assert any("command" in err.lower() for err in result["errors"])
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_missing_tests(self):
        """Test that config without tests fails validation."""
        config = {
            "command": "python3",
            "path": "test.py",
            "tests": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            result = validate.validate_config(temp_path)
            assert result["valid"] is False
            assert any("test" in err.lower() for err in result["errors"])
        finally:
            temp_path.unlink(missing_ok=True)

    def test_validate_missing_file(self):
        """Test that non-existent file fails validation."""
        result = validate.validate_config(Path("/nonexistent/config.json"))
        assert result["valid"] is False
        assert any("not found" in err.lower() for err in result["errors"])


class TestExportCommand:
    """Tests for the export command."""

    def test_generate_markdown(self):
        """Test markdown generation."""
        config = {
            "command": "python3",
            "path": "test.py",
            "tests": [
                {
                    "input": ["hello"],
                    "output": ["world"],
                    "timeout": 10
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            content = export.generate_markdown(config, temp_path, include_solutions=True)
            assert "# " in content  # Has title
            assert "Test Case 1" in content
            assert "Input:" in content
            assert "hello" in content
            assert "world" in content  # Solution included
        finally:
            temp_path.unlink(missing_ok=True)

    def test_generate_html(self):
        """Test HTML generation."""
        config = {
            "command": "python3",
            "path": "test.py",
            "tests": [
                {
                    "input": ["hello"],
                    "output": ["world"],
                    "timeout": 10
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            content = export.generate_html(config, temp_path, include_solutions=True)
            assert "<!DOCTYPE html>" in content
            assert "Test Case 1" in content
            assert "hello" in content
        finally:
            temp_path.unlink(missing_ok=True)

    def test_generate_markdown_without_solutions(self):
        """Test markdown generation without solutions."""
        config = {
            "command": "python3",
            "path": "test.py",
            "tests": [
                {
                    "input": ["hello"],
                    "output": ["secret"],
                    "timeout": 10
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = Path(f.name)
        
        try:
            content = export.generate_markdown(config, temp_path, include_solutions=False)
            assert "secret" not in content  # Solution not included
            assert "hidden" in content.lower()
        finally:
            temp_path.unlink(missing_ok=True)


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_template_python(self):
        """Test Python template generation."""
        config = generate.generate_template("python", "test.py")
        assert config["command"] == "python3"
        assert config["path"] == "test.py"
        assert len(config["tests"]) > 0

    def test_generate_template_c(self):
        """Test C template generation."""
        config = generate.generate_template("c", None)
        assert "compile_command" in config
        assert "gcc" in config["compile_command"]

    def test_generate_template_java(self):
        """Test Java template generation."""
        config = generate.generate_template("java", None)
        assert "compile_command" in config
        assert "javac" in config["compile_command"]
        assert "run_command" in config
        assert "java" in config["run_command"]


class TestInitCommand:
    """Tests for the init command."""

    def test_create_config(self):
        """Test config creation."""
        config = init.create_config("test_assignment", "python", "program.py")
        assert config["path"] == "program.py"
        assert config["command"] == "python3"
        assert len(config["tests"]) > 0

    def test_create_readme(self):
        """Test README creation."""
        readme = init.create_readme("test_assignment", "homework", "python", Path("/test"))
        assert "test_assignment" in readme
        assert "Python" in readme
        assert "Homework" in readme


class TestBatchReportGeneration:
    """Tests for batch report generation."""

    def test_generate_text_report(self):
        """Test text report generation."""
        results = [
            {
                "student_name": "Alice",
                "file_path": "alice.py",
                "total_tests": 10,
                "passed_tests": 10,
                "failed_tests": 0,
                "score": 100.0,
            },
            {
                "student_name": "Bob",
                "file_path": "bob.py",
                "total_tests": 10,
                "passed_tests": 5,
                "failed_tests": 5,
                "score": 50.0,
            },
        ]
        summary = {
            "generated_at": "2024-01-01T00:00:00",
            "config_file": "config.json",
            "total_students": 2,
            "average_score": 75.0,
            "highest_score": 100.0,
            "lowest_score": 50.0,
            "pass_rate": 50.0,
        }
        
        report = batch.generate_text_report(results, summary)
        assert "Alice" in report
        assert "Bob" in report
        assert "100" in report
        assert "50" in report
        assert "SUMMARY" in report

    def test_generate_csv_report(self):
        """Test CSV report generation."""
        results = [
            {
                "student_name": "Alice",
                "file_path": "alice.py",
                "total_tests": 10,
                "passed_tests": 10,
                "failed_tests": 0,
                "score": 100.0,
            },
        ]
        summary = {
            "generated_at": "2024-01-01T00:00:00",
            "config_file": "config.json",
        }
        
        report = batch.generate_csv_report(results, summary)
        assert "Alice" in report
        assert "100.0" in report
        assert "Student Name" in report

    def test_generate_html_report(self):
        """Test HTML report generation."""
        results = [
            {
                "student_name": "Alice",
                "file_path": "alice.py",
                "total_tests": 10,
                "passed_tests": 10,
                "failed_tests": 0,
                "score": 100.0,
            },
        ]
        summary = {
            "generated_at": "2024-01-01T00:00:00",
            "config_file": "config.json",
            "total_students": 1,
            "average_score": 100.0,
            "highest_score": 100.0,
            "lowest_score": 100.0,
            "pass_rate": 100.0,
        }
        
        report = batch.generate_html_report(results, summary)
        assert "<!DOCTYPE html>" in report
        assert "Alice" in report
        assert "score-high" in report  # High score class
