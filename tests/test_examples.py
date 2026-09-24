"""Every shipped example must produce the outcome its README documents."""

import os
import shutil
from pathlib import Path

import pytest

from testio.apps.cli.main import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

# (config relative to examples/, expected exit code, required toolchain)
CASES = [
    ("c_calculator/config.json", 0, "gcc"),
    ("c_hello_world/config.json", 0, "gcc"),
    ("execution_error/config.json", 1, None),
    ("failed_test/config.json", 1, None),
    ("homework_mode_demo/config.json", 0, None),
    ("interleaved_io/config.json", 0, None),
    ("java_hello_world/config.json", 0, "javac"),
    ("interleaved_io_complex/config.json", 0, None),
    ("multiple_inputs/config.json", 0, None),
    ("multiple_programs_tested/config.json", 1, None),
    ("multiple_tests/config.json", 0, None),
    ("multiple_tests_multiple_files/config.json", 1, None),
    ("no_input/config.json", 0, None),
    ("node_hello_world/config.json", 0, "node"),
    ("regex_output_matching/config.json", 0, None),
    ("regex_output_matching/config_mismatch.json", 1, None),
    ("ruby_hello_world/config.json", 0, "ruby"),
    ("single_input/config.json", 0, None),
    ("timeout_exceeded/config.json", 1, None),
]


def test_every_example_config_is_covered():
    shipped = {str(p.relative_to(EXAMPLES)) for p in EXAMPLES.glob("*/*.json")}
    assert shipped == {case[0] for case in CASES}


@pytest.mark.parametrize("config, expected_exit, toolchain", CASES)
def test_example(config, expected_exit, toolchain):
    if toolchain and shutil.which(toolchain) is None:
        pytest.skip(f"{toolchain} not installed")

    config_path = EXAMPLES / config
    cwd = os.getcwd()
    os.chdir(config_path.parent)
    try:
        assert main(["run", config_path.name, "-q"]) == expected_exit
    finally:
        os.chdir(cwd)
