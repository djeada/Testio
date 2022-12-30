from pathlib import Path

from src.cli.main import ConfigParser


def test_read_single_input_config_file(tmp_path):
    """
    Test reading config file with single input.
    """
    config_path = tmp_path / Path("test_config.json")

    exe_path = tmp_path / Path('program.py')
    exe_path.touch()

    with open(config_path, "w") as file:
        file.write(
            f'''
            {{
                "ProgramPath": "{exe_path.name}",
                "Timeout": 1,
                "Test1": {{
                    "input": ["3"],
                    "output": ["6"]
                }}
            }}
            '''
        )

    config_parser = ConfigParser(Path(config_path))
    assert config_parser.paths == [tmp_path / Path(f'{exe_path.name}')]
    assert config_parser.timeout == 1
    assert len(config_parser.tests) == 1
    assert config_parser.tests[0].input == "3"
    assert config_parser.tests[0].output == "6"


def test_read_multiple_tests_config_file(tmp_path):
    """	
    Test reading config file with multiple tests.
    """
    config_path = tmp_path / Path("test_config.json")

    exe_path = tmp_path / Path('python program.py')
    exe_path.touch()

    with open(config_path, "w") as file:
        file.write(
            f'''
            {{
                "ProgramPath": "{exe_path.name}",
                "Timeout": 1,
                "Test1": {{
                    "input": ["3"],
                    "output": ["6"]
                }},
                "Test2": {{
                    "input": ["4"],
                    "output": ["8"]
                }}
            }}
            '''
        )

    config_parser = ConfigParser(Path(config_path))
    assert config_parser.paths == [tmp_path / Path(f'{exe_path.name}')]
    assert config_parser.timeout == 1
    assert len(config_parser.tests) == 2
    assert config_parser.tests[0].input == "3"
    assert config_parser.tests[0].output == "6"
    assert config_parser.tests[1].input == "4"
    assert config_parser.tests[1].output == "8"
