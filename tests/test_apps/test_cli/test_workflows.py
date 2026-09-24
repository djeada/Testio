"""End-to-end CLI workflows: scaffold, generate, grade, export, report."""

import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from testio.apps.cli.commands.generate import generate_template
from testio.apps.cli.main import main
from testio.core.config_parser.parsers import validate_config_data

LANGUAGES = ["python", "c", "cpp", "java", "nodejs", "ruby", "go", "rust"]
TOOLCHAIN = {
    "python": "python3",
    "c": "gcc",
    "cpp": "g++",
    "java": "java",
    "nodejs": "node",
    "ruby": "ruby",
    "go": "go",
    "rust": "rustc",
}


@pytest.fixture
def in_tmp(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(cwd)


@pytest.mark.parametrize("language", LANGUAGES)
def test_generated_templates_are_valid(language):
    assert validate_config_data(generate_template(language, "prog")) == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_init_scaffold_solution_passes(in_tmp, language):
    """`testio init --with-solution` must produce a suite its own solution passes."""
    if shutil.which(TOOLCHAIN[language]) is None:
        pytest.skip(f"{TOOLCHAIN[language]} not installed")

    assert (
        main(["init", "hw", "-t", "homework", "-l", language, "--with-solution"]) == 0
    )
    config_path = in_tmp / "hw" / "config.json"
    config = json.loads(config_path.read_text())
    assert validate_config_data(config) == []

    config["path"] = "solution/"
    config_path.write_text(json.dumps(config))
    os.chdir(in_tmp / "hw")
    assert main(["run", "config.json", "-q"]) == 0


def _suite(tmp_path, tests, program="print(input())"):
    (tmp_path / "prog.py").write_text(program)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"command": "python3", "path": "prog.py", "tests": tests})
    )
    return config


def test_run_json_report(tmp_path, capsys):
    config = _suite(
        tmp_path,
        [{"input": ["a"], "output": ["a"]}, {"input": ["b"], "output": ["x"]}],
    )
    assert main(["run", str(config), "-f", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 1


def test_run_junit_and_tap_reports(tmp_path):
    config = _suite(tmp_path, [{"input": ["a"], "output": ["a"]}])
    junit = tmp_path / "out.xml"
    tap = tmp_path / "out.tap"
    assert main(["run", str(config), "-f", "junitxml", "-o", str(junit)]) == 0
    assert main(["run", str(config), "-f", "tap", "-o", str(tap)]) == 0
    ET.parse(junit)  # well-formed
    assert tap.read_text().startswith("TAP version 13")


def test_console_output_has_no_ansi_when_not_a_tty(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    config = _suite(tmp_path, [{"input": ["a"], "output": ["b"]}])
    main(["run", str(config)])
    assert "\033[" not in capsys.readouterr().out


def test_batch_grades_and_escapes_html(tmp_path):
    subs = tmp_path / "subs"
    subs.mkdir()
    (subs / "good.py").write_text("print(input())")
    (subs / "<img src=x onerror=alert(1)>.py").write_text("print('nope')")
    config = _suite(tmp_path, [{"input": ["hi"], "output": ["hi"]}])
    report = tmp_path / "report.html"

    assert (
        main(["batch", str(config), str(subs), "-f", "html", "-o", str(report), "-q"])
        == 0
    )

    html = report.read_text()
    assert "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_batch_compiles_c_submissions(tmp_path):
    if shutil.which("gcc") is None:
        pytest.skip("gcc not installed")
    subs = tmp_path / "subs"
    subs.mkdir()
    (subs / "ok.c").write_text('#include <stdio.h>\nint main(){puts("hi");}\n')
    (subs / "broken.c").write_text("int main( {\n")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "compile_command": "gcc {source} -o {output}",
                "path": "subs",
                "tests": [{"input": [], "output": ["hi"]}],
            }
        )
    )
    out = tmp_path / "grades.json"
    assert (
        main(["batch", str(config), str(subs), "-f", "json", "-o", str(out), "-q"]) == 0
    )
    scores = {
        r["student_name"]: r["score"] for r in json.loads(out.read_text())["results"]
    }
    assert scores == {"ok": 100.0, "broken": 0.0}


def test_export_escapes_html_and_can_hide_inputs(tmp_path):
    config = _suite(tmp_path, [{"input": ["a < b && c > d"], "output": ["<b>"]}])
    out = tmp_path / "out"

    assert (
        main(
            ["export", str(config), "-f", "html", "-o", str(out), "--include-solutions"]
        )
        == 0
    )
    html = (out / "config.html").read_text()
    assert "a &lt; b &amp;&amp; c &gt; d" in html
    assert "&lt;b&gt;" in html

    assert (
        main(["export", str(config), "-f", "md", "-o", str(out), "--no-include-inputs"])
        == 0
    )
    assert "a < b" not in (out / "config.md").read_text()


def test_export_pdf_without_backend_fails_loudly(tmp_path):
    try:
        import weasyprint  # noqa: F401

        pytest.skip("weasyprint installed")
    except ImportError:
        pass
    try:
        import pdfkit  # noqa: F401

        pytest.skip("pdfkit installed")
    except ImportError:
        pass
    config = _suite(tmp_path, [{"input": [], "output": []}])
    assert main(["export", str(config), "-f", "pdf", "-o", str(tmp_path / "o")]) == 1
    assert (tmp_path / "o" / "config.html").exists()


def test_validate_rejects_non_object_config(tmp_path):
    config = tmp_path / "config.json"
    config.write_text("[1, 2]")
    assert main(["validate", str(config)]) == 1


def test_validate_accepts_schema_default_timeout(tmp_path):
    config = _suite(tmp_path, [{"input": ["a"], "output": ["a"]}])
    assert main(["validate", str(config)]) == 0


def test_generate_non_interactive_writes_valid_config(tmp_path):
    out = tmp_path / "gen.json"
    assert main(["generate", str(out), "-t", "c", "-n"]) == 0
    assert validate_config_data(json.loads(Path(out).read_text())) == []
