"""
Export command module - export problem descriptions and results to various formats.
Teachers can use this to generate printable materials for students.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the export command parser to the subparsers."""
    parser = subparsers.add_parser(
        "export",
        help="Export problems/configs to PDF, HTML, or Markdown",
        description="Convert problem descriptions and configurations to printable formats.",
    )
    parser.add_argument(
        "config_files",
        type=str,
        nargs="+",
        help="Path(s) to the JSON config file(s) to export",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["pdf", "html", "md", "all"],
        default="html",
        help="Output format (default: html)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        help="Document title",
    )
    parser.add_argument(
        "--include-solutions",
        action="store_true",
        help="Include expected outputs (for teacher reference)",
    )
    parser.add_argument(
        "--include-inputs",
        action="store_true",
        default=True,
        help="Include test inputs (default: True)",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Combine all configs into a single document",
    )
    parser.set_defaults(func=execute)


def load_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse a configuration file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {config_path}: {e}")
        return None


def generate_markdown(
    config: Dict[str, Any],
    config_path: Path,
    include_solutions: bool = False,
    include_inputs: bool = True,
    title: Optional[str] = None,
) -> str:
    """
    Generate Markdown content from a configuration.

    :param config: The configuration dictionary.
    :param config_path: Path to the configuration file.
    :param include_solutions: Whether to include expected outputs.
    :param include_inputs: Whether to include test inputs.
    :param title: Optional title for the document.
    :return: Markdown string.
    """
    lines = []

    # Title
    doc_title = title or config_path.stem.replace("_", " ").title()
    lines.append(f"# {doc_title}")
    lines.append("")

    # Problem info
    lines.append("## Problem Information")
    lines.append("")

    program_path = config.get("path", "program")
    lines.append(f"**Program:** `{program_path}`")
    lines.append("")

    # Command info
    if config.get("command"):
        lines.append(f"**Execution command:** `{config['command']}`")
    if config.get("run_command"):
        lines.append(f"**Run command:** `{config['run_command']}`")
    if config.get("compile_command"):
        lines.append(f"**Compile command:** `{config['compile_command']}`")
    lines.append("")

    # Test cases
    lines.append("## Test Cases")
    lines.append("")

    tests = config.get("tests", [])
    for i, test in enumerate(tests, 1):
        lines.append(f"### Test Case {i}")
        lines.append("")

        # Timeout
        timeout = test.get("timeout", "N/A")
        lines.append(f"**Timeout:** {timeout} seconds")
        lines.append("")

        # Special flags
        flags = []
        if test.get("interleaved"):
            flags.append("Interactive (interleaved I/O)")
        if test.get("unordered"):
            flags.append("Unordered output")
        if test.get("use_regex"):
            flags.append("Regex matching")
        if flags:
            lines.append(f"**Mode:** {', '.join(flags)}")
            lines.append("")

        # Input
        if include_inputs:
            inp = test.get("input", [])
            if isinstance(inp, str):
                inp = [inp] if inp else []
            
            lines.append("**Input:**")
            lines.append("```")
            if inp:
                for line in inp:
                    lines.append(line)
            else:
                lines.append("(no input)")
            lines.append("```")
            lines.append("")

        # Expected output (only if solutions are included)
        if include_solutions:
            out = test.get("output", [])
            if isinstance(out, str):
                out = [out] if out else []
            
            lines.append("**Expected Output:**")
            lines.append("```")
            if out:
                for line in out:
                    lines.append(line)
            else:
                lines.append("(no output expected)")
            lines.append("```")
            lines.append("")
        else:
            lines.append("**Expected Output:** *(hidden)*")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated by Testio on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


def generate_html(
    config: Dict[str, Any],
    config_path: Path,
    include_solutions: bool = False,
    include_inputs: bool = True,
    title: Optional[str] = None,
) -> str:
    """
    Generate HTML content from a configuration.

    :param config: The configuration dictionary.
    :param config_path: Path to the configuration file.
    :param include_solutions: Whether to include expected outputs.
    :param include_inputs: Whether to include test inputs.
    :param title: Optional title for the document.
    :return: HTML string.
    """
    doc_title = title or config_path.stem.replace("_", " ").title()
    tests = config.get("tests", [])

    test_cases_html = []
    for i, test in enumerate(tests, 1):
        inp = test.get("input", [])
        if isinstance(inp, str):
            inp = [inp] if inp else []
        out = test.get("output", [])
        if isinstance(out, str):
            out = [out] if out else []

        flags = []
        if test.get("interleaved"):
            flags.append("Interactive")
        if test.get("unordered"):
            flags.append("Unordered")
        if test.get("use_regex"):
            flags.append("Regex")

        input_html = ""
        if include_inputs:
            input_lines = "\n".join(inp) if inp else "(no input)"
            input_html = f"""
            <div class="section">
                <h4>Input:</h4>
                <pre>{input_lines}</pre>
            </div>
            """

        output_html = ""
        if include_solutions:
            output_lines = "\n".join(out) if out else "(no output expected)"
            output_html = f"""
            <div class="section">
                <h4>Expected Output:</h4>
                <pre>{output_lines}</pre>
            </div>
            """
        else:
            output_html = """
            <div class="section">
                <h4>Expected Output:</h4>
                <p><em>(hidden)</em></p>
            </div>
            """

        flags_html = f'<span class="flags">({", ".join(flags)})</span>' if flags else ""

        test_cases_html.append(f"""
        <div class="test-case">
            <h3>Test Case {i} {flags_html}</h3>
            <p><strong>Timeout:</strong> {test.get('timeout', 'N/A')} seconds</p>
            {input_html}
            {output_html}
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{doc_title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .test-case {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .section h4 {{
            margin: 10px 0 5px 0;
            color: #495057;
        }}
        pre {{
            background: #2d3436;
            color: #dfe6e9;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 14px;
        }}
        .flags {{
            font-size: 12px;
            color: #6c757d;
            font-weight: normal;
        }}
        .info {{
            background: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 12px;
        }}
        @media print {{
            .test-case {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <h1>{doc_title}</h1>
    
    <div class="info">
        <strong>Program:</strong> <code>{config.get('path', 'program')}</code><br>
        {'<strong>Command:</strong> <code>' + config.get('command', '') + '</code><br>' if config.get('command') else ''}
        {'<strong>Compile:</strong> <code>' + config.get('compile_command', '') + '</code><br>' if config.get('compile_command') else ''}
        <strong>Total test cases:</strong> {len(tests)}
    </div>
    
    <h2>Test Cases</h2>
    {''.join(test_cases_html)}
    
    <div class="footer">
        Generated by Testio on {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</body>
</html>
"""
    return html


def generate_pdf(
    html_content: str,
    output_path: Path,
) -> bool:
    """
    Generate PDF from HTML content.
    
    Note: This requires wkhtmltopdf or weasyprint to be installed.
    Falls back to saving HTML if PDF generation is not available.

    :param html_content: HTML string to convert.
    :param output_path: Path for the output PDF file.
    :return: True if successful, False otherwise.
    """
    try:
        # Try weasyprint first
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(str(output_path))
        return True
    except ImportError:
        pass

    try:
        # Try pdfkit (wkhtmltopdf)
        import pdfkit
        pdfkit.from_string(html_content, str(output_path))
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: PDF generation failed: {e}")

    print(
        "Note: PDF generation requires 'weasyprint' or 'pdfkit' package.\n"
        "Install with: pip install weasyprint\n"
        "Falling back to HTML output."
    )
    return False


def execute(args: argparse.Namespace) -> int:
    """
    Execute the export command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    configs = []
    for config_file in args.config_files:
        config_path = Path(config_file)
        config = load_config(config_path)
        if config:
            configs.append((config_path, config))

    if not configs:
        print("Error: No valid configuration files found.")
        return 1

    print(f"Exporting {len(configs)} configuration(s)...")

    formats_to_generate = []
    if args.format == "all":
        formats_to_generate = ["html", "md", "pdf"]
    else:
        formats_to_generate = [args.format]

    for config_path, config in configs:
        base_name = config_path.stem

        for fmt in formats_to_generate:
            if fmt == "md":
                content = generate_markdown(
                    config,
                    config_path,
                    include_solutions=args.include_solutions,
                    include_inputs=args.include_inputs,
                    title=args.title,
                )
                output_path = output_dir / f"{base_name}.md"
                with open(output_path, "w") as f:
                    f.write(content)
                print(f"  Created: {output_path}")

            elif fmt == "html":
                content = generate_html(
                    config,
                    config_path,
                    include_solutions=args.include_solutions,
                    include_inputs=args.include_inputs,
                    title=args.title,
                )
                output_path = output_dir / f"{base_name}.html"
                with open(output_path, "w") as f:
                    f.write(content)
                print(f"  Created: {output_path}")

            elif fmt == "pdf":
                html_content = generate_html(
                    config,
                    config_path,
                    include_solutions=args.include_solutions,
                    include_inputs=args.include_inputs,
                    title=args.title,
                )
                output_path = output_dir / f"{base_name}.pdf"
                if generate_pdf(html_content, output_path):
                    print(f"  Created: {output_path}")
                else:
                    # Fallback to HTML
                    html_path = output_dir / f"{base_name}.html"
                    with open(html_path, "w") as f:
                        f.write(html_content)
                    print(f"  Created: {html_path} (PDF fallback)")

    print("Export complete!")
    return 0
