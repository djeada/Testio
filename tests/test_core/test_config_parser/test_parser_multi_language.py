"""
Tests for config parser with compile_command and run_command fields
"""
import json
import tempfile
import pytest
from pathlib import Path

from src.core.config_parser.parsers import ConfigParser
from src.core.config_parser.data import TestData, TestSuiteConfig


def test_parse_config_with_compile_command():
    """Test parsing a config file with compile_command"""
    config_data = {
        "compile_command": "gcc {source} -o {output}",
        "run_command": "",
        "path": "test.c",
        "tests": [
            {
                "input": [],
                "output": ["Hello World"],
                "timeout": 10
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert result.compile_command == "gcc {source} -o {output}"
    assert result.run_command == ""
    assert len(result.tests) == 1


def test_parse_config_with_run_command():
    """Test parsing a config file with run_command"""
    config_data = {
        "run_command": "node",
        "path": "test.js",
        "tests": [
            {
                "input": [],
                "output": ["Hello"],
                "timeout": 10
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert result.run_command == "node"
    assert result.compile_command == ""
    assert len(result.tests) == 1


def test_parse_config_with_both_compile_and_run():
    """Test parsing a config with both compile_command and run_command"""
    config_data = {
        "compile_command": "javac {source}",
        "run_command": "java",
        "path": "Test.java",
        "tests": [
            {
                "input": [],
                "output": ["Java output"],
                "timeout": 10
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert result.compile_command == "javac {source}"
    assert result.run_command == "java"


def test_parse_config_backward_compatible():
    """Test that old config format with only 'command' still works"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["input1"],
                "output": ["output1"],
                "timeout": 10
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert result.command == "python3"
    assert result.compile_command == ""
    assert result.run_command == ""


def test_validate_config_with_run_command_only():
    """Test validation accepts config with only run_command"""
    config_data = {
        "run_command": "node",
        "path": "test.js",
        "tests": [
            {
                "input": [],
                "output": ["test"],
                "timeout": 5
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        is_valid = parser.validate(Path(temp_path))
        assert is_valid
    finally:
        Path(temp_path).unlink()


def test_validate_config_with_command_only():
    """Test validation accepts config with only command (backward compatibility)"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": [],
                "output": ["test"],
                "timeout": 5
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        is_valid = parser.validate(Path(temp_path))
        assert is_valid
    finally:
        Path(temp_path).unlink()


def test_validate_config_without_command_or_run_command():
    """Test validation rejects config without command or run_command"""
    config_data = {
        "path": "test.py",
        "tests": [
            {
                "input": [],
                "output": ["test"],
                "timeout": 5
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        is_valid = parser.validate(Path(temp_path))
        assert not is_valid
    finally:
        Path(temp_path).unlink()


def test_parse_config_file_with_compile_command():
    """Test parsing an actual config file with compile_command"""
    config_data = {
        "compile_command": "gcc {source} -o {output}",
        "run_command": "",
        "path": "hello.c",
        "tests": [
            {
                "input": [],
                "output": ["Hello"],
                "timeout": 5
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        result = parser.parse_from_path(Path(temp_path))
        
        assert result is not None
        assert result.compile_command == "gcc {source} -o {output}"
    finally:
        Path(temp_path).unlink()


def test_parse_config_empty_strings_for_optional_fields():
    """Test that optional compile_command and run_command default to empty strings"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": [],
                "output": ["test"],
                "timeout": 5
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert result.compile_command == ""
    assert result.run_command == ""
