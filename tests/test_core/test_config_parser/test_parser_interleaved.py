"""
Tests for config parser with interleaved flag
"""
import json
import tempfile
import pytest
from pathlib import Path

from src.core.config_parser.parsers import ConfigParser
from src.core.config_parser.data import TestData


def test_parse_config_with_interleaved_flag():
    """Test parsing a config file with interleaved flag set to true"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["input1", "input2"],
                "output": ["output1", "output2"],
                "timeout": 10,
                "interleaved": True
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert len(result.tests) == 1
    assert result.tests[0].interleaved is True


def test_parse_config_without_interleaved_flag():
    """Test parsing a config file without interleaved flag (should default to False)"""
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
    assert len(result.tests) == 1
    assert not result.tests[0].interleaved


def test_parse_config_with_interleaved_false():
    """Test parsing a config file with interleaved explicitly set to false"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["input1"],
                "output": ["output1"],
                "timeout": 10,
                "interleaved": False
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert len(result.tests) == 1
    assert not result.tests[0].interleaved


def test_parse_config_mixed_interleaved():
    """Test parsing a config with multiple tests, some interleaved and some not"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["input1"],
                "output": ["output1"],
                "timeout": 10,
                "interleaved": True
            },
            {
                "input": ["input2"],
                "output": ["output2"],
                "timeout": 10,
                "interleaved": False
            },
            {
                "input": ["input3"],
                "output": ["output3"],
                "timeout": 10
            }
        ]
    }
    
    parser = ConfigParser()
    result = parser.parse_from_json(config_data)
    
    assert result is not None
    assert len(result.tests) == 3
    assert result.tests[0].interleaved
    assert not result.tests[1].interleaved
    assert not result.tests[2].interleaved  # Default


def test_parse_config_file_with_interleaved():
    """Test parsing an actual config file with interleaved flag"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["Alice", "25"],
                "output": ["Hello", "You are 25"],
                "timeout": 5,
                "interleaved": True
            }
        ]
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        result = parser.parse_from_path(Path(temp_path))
        
        assert result is not None
        assert result.tests[0].interleaved is True
    finally:
        Path(temp_path).unlink()


def test_validate_config_with_interleaved():
    """Test that validation accepts configs with interleaved flag"""
    config_data = {
        "command": "python3",
        "path": "test.py",
        "tests": [
            {
                "input": ["input1"],
                "output": ["output1"],
                "timeout": 10,
                "interleaved": True
            }
        ]
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        parser = ConfigParser()
        is_valid = parser.validate(Path(temp_path))
        
        assert is_valid
    finally:
        Path(temp_path).unlink()
