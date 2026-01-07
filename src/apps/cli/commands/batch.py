"""
Batch command module - test multiple student submissions.
Teachers can use this to grade homework assignments in batch.
"""

import argparse
import json
import csv
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List, Dict, Any
from datetime import datetime

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import (
    ComparisonResult,
    ExecutionManagerFactory,
    ExecutionManagerInputData,
    ComparisonOutputData,
)
from src.core.execution.manager import ExecutionManager


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the batch command parser to the subparsers."""
    parser = subparsers.add_parser(
        "batch",
        help="Test multiple student submissions in batch",
        description="Grade multiple student program submissions against test cases.",
    )
    parser.add_argument(
        "config_file",
        type=str,
        help="Path to the JSON config file with test cases",
    )
    parser.add_argument(
        "submissions",
        type=str,
        nargs="+",
        help="Path(s) to student submission files or directories",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for the report",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["json", "csv", "text", "html"],
        default="text",
        help="Report output format (default: text)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress detailed output during testing",
    )
    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        default=None,
        help="Number of parallel workers (default: auto)",
    )
    parser.set_defaults(func=execute)


def process_submission(
    args: Tuple[str, str, List[ExecutionManagerInputData]]
) -> Dict[str, Any]:
    """
    Process a single student submission.

    :param args: Tuple of (student_name, file_path, execution_data)
    :return: Dictionary with student results.
    """
    student_name, file_path, execution_data = args
    manager = ExecutionManager()
    results = []

    for data in execution_data:
        result = manager.run(data)
        results.append(result)

    total_tests = len(results)
    passed_tests = len(
        [r for r in results if r.result == ComparisonResult.MATCH]
    )
    score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    return {
        "student_name": student_name,
        "file_path": file_path,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "score": round(score, 2),
        "test_results": [
            {
                "input": r.input,
                "expected_output": r.expected_output,
                "actual_output": r.output,
                "error": r.error,
                "passed": r.result == ComparisonResult.MATCH,
                "result_type": str(r.result),
            }
            for r in results
        ],
    }


def collect_submissions(paths: List[str]) -> List[Tuple[str, str]]:
    """
    Collect all submission files from given paths.

    :param paths: List of file or directory paths.
    :return: List of (student_name, file_path) tuples.
    """
    submissions = []

    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            student_name = path.stem
            submissions.append((student_name, str(path)))
        elif path.is_dir():
            for file in path.iterdir():
                if file.is_file() and not file.name.startswith("."):
                    student_name = file.stem
                    submissions.append((student_name, str(file)))
        else:
            print(f"Warning: Path not found: {path}")

    return sorted(submissions, key=lambda x: x[0])


def generate_text_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """Generate a text format report."""
    lines = []
    lines.append("=" * 70)
    lines.append("BATCH TEST RESULTS")
    lines.append("=" * 70)
    lines.append(f"Generated: {summary['generated_at']}")
    lines.append(f"Config: {summary['config_file']}")
    lines.append("")

    # Summary table
    lines.append("-" * 70)
    lines.append(f"{'Student':<30} {'Score':>10} {'Passed':>10} {'Failed':>10}")
    lines.append("-" * 70)

    for result in results:
        lines.append(
            f"{result['student_name']:<30} "
            f"{result['score']:>9.1f}% "
            f"{result['passed_tests']:>10} "
            f"{result['failed_tests']:>10}"
        )

    lines.append("-" * 70)
    lines.append("")
    lines.append("SUMMARY")
    lines.append(f"  Total students: {summary['total_students']}")
    lines.append(f"  Average score: {summary['average_score']:.2f}%")
    lines.append(f"  Highest score: {summary['highest_score']:.2f}%")
    lines.append(f"  Lowest score: {summary['lowest_score']:.2f}%")
    lines.append(f"  Pass rate (>= 60%): {summary['pass_rate']:.2f}%")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_csv_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """Generate a CSV format report."""
    import io
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Student Name",
        "File Path",
        "Score (%)",
        "Passed Tests",
        "Failed Tests",
        "Total Tests",
    ])

    # Data rows
    for result in results:
        writer.writerow([
            result["student_name"],
            result["file_path"],
            result["score"],
            result["passed_tests"],
            result["failed_tests"],
            result["total_tests"],
        ])

    return output.getvalue()


def generate_html_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """Generate an HTML format report."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Batch Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ margin-top: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .score-high {{ background-color: #c8e6c9; }}
        .score-mid {{ background-color: #fff9c4; }}
        .score-low {{ background-color: #ffcdd2; }}
    </style>
</head>
<body>
    <h1>Batch Test Results</h1>
    <p>Generated: {generated_at}</p>
    <p>Config: {config_file}</p>
    
    <table>
        <tr>
            <th>Student</th>
            <th>Score</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Total</th>
        </tr>
        {rows}
    </table>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li>Total students: {total_students}</li>
            <li>Average score: {average_score:.2f}%</li>
            <li>Highest score: {highest_score:.2f}%</li>
            <li>Lowest score: {lowest_score:.2f}%</li>
            <li>Pass rate (>= 60%): {pass_rate:.2f}%</li>
        </ul>
    </div>
</body>
</html>
"""
    
    rows = []
    for result in results:
        score_class = (
            "score-high" if result["score"] >= 80
            else "score-mid" if result["score"] >= 60
            else "score-low"
        )
        rows.append(
            f'<tr class="{score_class}">'
            f'<td>{result["student_name"]}</td>'
            f'<td>{result["score"]:.1f}%</td>'
            f'<td class="pass">{result["passed_tests"]}</td>'
            f'<td class="fail">{result["failed_tests"]}</td>'
            f'<td>{result["total_tests"]}</td>'
            f'</tr>'
        )

    return html.format(
        rows="\n        ".join(rows),
        **summary,
    )


def execute(args: argparse.Namespace) -> int:
    """
    Execute the batch command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
    config_path = Path(args.config_file)

    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        return 1

    # Parse configuration
    parser = ConfigParser()
    try:
        test_suite_config = parser.parse_from_path(config_path)
    except Exception as e:
        print(f"Error: Failed to parse config file: {e}")
        return 1

    # Collect submissions
    submissions = collect_submissions(args.submissions)
    if not submissions:
        print("Error: No submission files found.")
        return 1

    if not args.quiet:
        print(f"Found {len(submissions)} submissions to test.")

    # Prepare execution data for each submission
    pool_args = []
    for student_name, file_path in submissions:
        # Create execution data using the student's file
        execution_data = ExecutionManagerFactory._create_execution_manager_data(
            test_suite_config, file_path
        )
        pool_args.append((student_name, file_path, execution_data))

    # Process submissions in parallel
    if not args.quiet:
        print("Running tests...")

    max_workers = args.parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_submission, pool_args))

    # Calculate summary statistics
    scores = [r["score"] for r in results]
    passing = [r for r in results if r["score"] >= 60]

    summary = {
        "generated_at": datetime.now().isoformat(),
        "config_file": str(config_path),
        "total_students": len(results),
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "pass_rate": (len(passing) / len(results) * 100) if results else 0,
    }

    # Generate report
    if args.format == "json":
        report = json.dumps({"summary": summary, "results": results}, indent=2)
    elif args.format == "csv":
        report = generate_csv_report(results, summary)
    elif args.format == "html":
        report = generate_html_report(results, summary)
    else:  # text
        report = generate_text_report(results, summary)

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)

    return 0
