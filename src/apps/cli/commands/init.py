"""
Init command module - initialize a new problem or homework structure.
Teachers can use this to set up a new assignment directory.
"""

import argparse
import json
from pathlib import Path
from typing import Optional


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the init command parser to the subparsers."""
    parser = subparsers.add_parser(
        "init",
        help="Initialize a new problem or homework directory structure",
        description="Create a directory structure for a new programming assignment.",
    )
    parser.add_argument(
        "name",
        type=str,
        help="Name of the assignment/problem",
    )
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        choices=["homework", "exam", "lab", "exercise"],
        default="homework",
        help="Type of assignment (default: homework)",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        choices=["python", "c", "cpp", "java", "nodejs", "ruby", "go", "rust"],
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help="Parent directory for the assignment (default: current directory)",
    )
    parser.add_argument(
        "--with-solution",
        action="store_true",
        help="Include a solution template",
    )
    parser.add_argument(
        "--with-readme",
        action="store_true",
        default=True,
        help="Include a README file (default: True)",
    )
    parser.set_defaults(func=execute)


# Language configurations
LANGUAGE_CONFIGS = {
    "python": {
        "extension": ".py",
        "command": "python3",
        "sample_code": '''"""
Student submission for: {name}
Name: [Your Name]
Date: [Date]
"""

def main():
    # TODO: Implement your solution here
    pass


if __name__ == "__main__":
    main()
''',
        "solution_code": '''"""
Solution for: {name}
"""

def main():
    # Example solution
    data = input()
    print(f"Hello, {{data}}!")


if __name__ == "__main__":
    main()
''',
    },
    "c": {
        "extension": ".c",
        "compile_command": "gcc {source} -o {output}",
        "sample_code": '''/*
 * Student submission for: {name}
 * Name: [Your Name]
 * Date: [Date]
 */

#include <stdio.h>

int main() {{
    // TODO: Implement your solution here
    
    return 0;
}}
''',
        "solution_code": '''/*
 * Solution for: {name}
 */

#include <stdio.h>

int main() {{
    char name[100];
    scanf("%s", name);
    printf("Hello, %s!\\n", name);
    return 0;
}}
''',
    },
    "cpp": {
        "extension": ".cpp",
        "compile_command": "g++ {source} -o {output}",
        "sample_code": '''/*
 * Student submission for: {name}
 * Name: [Your Name]
 * Date: [Date]
 */

#include <iostream>
#include <string>

using namespace std;

int main() {{
    // TODO: Implement your solution here
    
    return 0;
}}
''',
        "solution_code": '''/*
 * Solution for: {name}
 */

#include <iostream>
#include <string>

using namespace std;

int main() {{
    string name;
    cin >> name;
    cout << "Hello, " << name << "!" << endl;
    return 0;
}}
''',
    },
    "java": {
        "extension": ".java",
        "compile_command": "javac {source}",
        "run_command": "java",
        "sample_code": '''/*
 * Student submission for: {name}
 * Name: [Your Name]
 * Date: [Date]
 */

import java.util.Scanner;

public class Solution {{
    public static void main(String[] args) {{
        // TODO: Implement your solution here
        Scanner scanner = new Scanner(System.in);
        
    }}
}}
''',
        "solution_code": '''/*
 * Solution for: {name}
 */

import java.util.Scanner;

public class Solution {{
    public static void main(String[] args) {{
        Scanner scanner = new Scanner(System.in);
        String name = scanner.nextLine();
        System.out.println("Hello, " + name + "!");
    }}
}}
''',
    },
    "nodejs": {
        "extension": ".js",
        "run_command": "node",
        "sample_code": '''/*
 * Student submission for: {name}
 * Name: [Your Name]
 * Date: [Date]
 */

const readline = require('readline');

const rl = readline.createInterface({{
    input: process.stdin,
    output: process.stdout,
    terminal: false
}});

// TODO: Implement your solution here
rl.on('line', (line) => {{
    // Process input
}});
''',
        "solution_code": '''/*
 * Solution for: {name}
 */

const readline = require('readline');

const rl = readline.createInterface({{
    input: process.stdin,
    output: process.stdout,
    terminal: false
}});

rl.on('line', (line) => {{
    console.log(`Hello, ${{line}}!`);
}});
''',
    },
    "ruby": {
        "extension": ".rb",
        "run_command": "ruby",
        "sample_code": '''# Student submission for: {name}
# Name: [Your Name]
# Date: [Date]

# TODO: Implement your solution here
''',
        "solution_code": '''# Solution for: {name}

name = gets.chomp
puts "Hello, #{{name}}!"
''',
    },
    "go": {
        "extension": ".go",
        "compile_command": "go build -o {output} {source}",
        "sample_code": '''// Student submission for: {name}
// Name: [Your Name]
// Date: [Date]

package main

import "fmt"

func main() {{
    // TODO: Implement your solution here
}}
''',
        "solution_code": '''// Solution for: {name}

package main

import "fmt"

func main() {{
    var name string
    fmt.Scan(&name)
    fmt.Printf("Hello, %s!\\n", name)
}}
''',
    },
    "rust": {
        "extension": ".rs",
        "compile_command": "rustc {source} -o {output}",
        "sample_code": '''// Student submission for: {name}
// Name: [Your Name]
// Date: [Date]

use std::io;

fn main() {{
    // TODO: Implement your solution here
}}
''',
        "solution_code": '''// Solution for: {name}

use std::io;

fn main() {{
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    println!("Hello, {{}}!", input.trim());
}}
''',
    },
}


def create_readme(
    name: str,
    assignment_type: str,
    language: str,
    assignment_dir: Path,
) -> str:
    """Generate README content for the assignment."""
    lang_config = LANGUAGE_CONFIGS[language]

    return f"""# {name}

## Assignment Type
{assignment_type.title()}

## Description
<!-- Add problem description here -->

TODO: Describe the problem that students need to solve.

## Requirements
- Write a program in {language.title()}
- Your program should read input from standard input
- Your program should write output to standard output

## Input Format
<!-- Describe the input format -->

## Output Format
<!-- Describe the expected output format -->

## Example

### Input
```
example input
```

### Output
```
expected output
```

## Submission
1. Create your solution in a file named `solution{lang_config['extension']}`
2. Test your solution locally
3. Submit your file

## Testing Your Solution
You can test your solution using Testio:

```bash
python src/main.py cli run {assignment_dir}/config.json
```

## Notes
- Make sure your program handles edge cases
- Test with the provided examples before submitting
"""


def create_config(
    name: str,
    language: str,
    program_path: str,
) -> dict:
    """Generate configuration for the assignment."""
    lang_config = LANGUAGE_CONFIGS[language]
    
    config = {
        "path": program_path,
        "tests": [
            {
                "input": ["World"],
                "output": ["Hello, World!"],
                "timeout": 10
            },
            {
                "input": ["Testio"],
                "output": ["Hello, Testio!"],
                "timeout": 10
            }
        ]
    }

    # Add language-specific execution config
    if "command" in lang_config:
        config["command"] = lang_config["command"]
    if "run_command" in lang_config:
        config["run_command"] = lang_config["run_command"]
    if "compile_command" in lang_config:
        config["compile_command"] = lang_config["compile_command"]

    return config


def execute(args: argparse.Namespace) -> int:
    """
    Execute the init command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
    # Create assignment directory
    base_dir = Path(args.output_dir)
    assignment_dir = base_dir / args.name

    if assignment_dir.exists():
        print(f"Error: Directory '{assignment_dir}' already exists.")
        return 1

    # Get language configuration
    lang_config = LANGUAGE_CONFIGS[args.language]
    extension = lang_config["extension"]

    # Create directory structure
    print(f"Creating assignment structure for '{args.name}'...")

    # Main directory
    assignment_dir.mkdir(parents=True)
    print(f"  Created: {assignment_dir}/")

    # Submissions directory (for student files)
    submissions_dir = assignment_dir / "submissions"
    submissions_dir.mkdir()
    print(f"  Created: {submissions_dir}/")

    # Create template file for students
    template_file = assignment_dir / f"template{extension}"
    template_content = lang_config["sample_code"].format(name=args.name)
    template_file.write_text(template_content)
    print(f"  Created: {template_file}")

    # Create solution file if requested
    if args.with_solution:
        solution_dir = assignment_dir / "solution"
        solution_dir.mkdir()
        solution_file = solution_dir / f"solution{extension}"
        solution_content = lang_config["solution_code"].format(name=args.name)
        solution_file.write_text(solution_content)
        print(f"  Created: {solution_file}")

    # Create configuration file
    config_file = assignment_dir / "config.json"
    # Point to submissions directory for batch testing
    config = create_config(args.name, args.language, "submissions/")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
    print(f"  Created: {config_file}")

    # Create README if requested
    if args.with_readme:
        readme_file = assignment_dir / "README.md"
        readme_content = create_readme(
            args.name, args.type, args.language, assignment_dir
        )
        readme_file.write_text(readme_content)
        print(f"  Created: {readme_file}")

    # Print summary
    print("\n" + "=" * 50)
    print(f"Assignment '{args.name}' created successfully!")
    print("=" * 50)
    print("\nDirectory structure:")
    print(f"  {assignment_dir}/")
    print(f"    ├── config.json          # Test configuration")
    print(f"    ├── template{extension:<12} # Student template")
    print(f"    ├── submissions/          # Place student files here")
    if args.with_solution:
        print(f"    └── solution/             # Reference solution")
        print(f"        └── solution{extension}")
    if args.with_readme:
        print(f"    └── README.md             # Problem description")

    print("\nNext steps:")
    print(f"  1. Edit {assignment_dir}/README.md to add problem description")
    print(f"  2. Edit {assignment_dir}/config.json to add test cases")
    print(f"  3. Place student submissions in {submissions_dir}/")
    print(f"  4. Run: python src/main.py cli batch {config_file} {submissions_dir}")

    return 0
