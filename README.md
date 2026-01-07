# Testio

<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

Testio is a flexible and powerful testing framework that uses multiprocessing to verify the standard output of applications. With its two convenient interfaces: CLI and web server, you can test applications with a variety of configurations and inputs on a large scale.

![testio](https://github.com/djeada/Testio/assets/37275728/ab799306-e5b3-457c-bb69-0a4322ee6ad2)

## Overview
Testio is a tool that was created to make testing the standard output of applications effortless and efficient. Its user-friendly design makes it a valuable tool for teachers, who can use it to assess the programs submitted by their students and ensure they meet the intended requirements.

As a teacher, you can utilize Testio to automate the evaluation process of homework tasks and exams. By providing a set of inputs, the tool will execute the programs or scripts submitted by students and compare the results to the expected output. Testio will then generate a report for the teacher, providing a clear and concise assessment of each program's functionality.

In addition to its educational benefits, Testio is also a useful tool for industry professionals in CI/CD pipelines. By running end-to-end tests on an application, you can use Testio to verify that it operates as intended. Whether you are testing scripts or compiling executables, the tool can help you validate the output of your program for a given set of inputs. If a test fails, Testio will exit with a non-zero exit code, signaling that the application needs attention. If all tests pass, the tool will exit with a zero exit code, indicating that the application is working as expected.

## Key Features
- Easy and efficient testing of application outputs
- Two user-friendly interfaces: CLI and web server
- Ideal for teachers to check student programs and homework assignments
- Can be integrated into CI/CD pipelines in the industry
- Compares application output against expected output
- **Multi-language support**: Test programs written in any language (Python, C, C++, Java, JavaScript, Ruby, Go, Rust, etc.)
- **Automatic compilation**: Compiles programs before testing for compiled languages
- **Support for interleaved input/output testing** for interactive programs
- **Support for non-deterministic output** where line order doesn't matter
- Option to generate a PDF report of results
- FastAPI-based REST API for easy integration with other tools

## Requirements

* Python 3.8+
* fastapi
* uvicorn

## Installation

The easiest way to install Testio is to use virtualenv:


    $ git clone https://github.com/djeada/Testio.git
    $ cd Testio
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt

## Usage

Testio provides two different interfaces for running tests: a command-line interface (CLI) and a web interface using a FastAPI server. Both interfaces provide similar functionality but allow you to interact with Testio in different ways.

### Command-line interface

To use the CLI, run the main.py script with the cli argument and pass the path to the config file as an argument:

    $ python src/main.py cli path/to/config_file.json

The CLI will run the tests specified in the config file and display the results on the command line. You can also generate a PDF report containing the results by passing the --report flag:

    $ python src/main.py cli path/to/config_file.json --report

### FastAPI server

To use the web interface, run the main.py script with the fastapi argument:

    $ python src/main.py fastapi

This will start the FastAPI server and serve the web interface at http://localhost:5000. You can specify the path to the config file as an argument:

    $ python src/main.py fastapi path/to/config_file.json

You can also customize the host and port:

    $ python src/main.py fastapi --host 0.0.0.0 --port 8000

To update the test suite, use the following API endpoint:

    curl -X POST \
    --header "Content-Type: application/json" \
    -d @/path/to/file.json \
    http://localhost:5000/update_test_suite

The FastAPI server also provides automatic API documentation at:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## Configuration

To configure the script, you need to create a JSON file with the following structure:

    {
        "command": "python",
        "path": "path/to/script.py",
        "tests": [
            {
                "input": "input data",
                "output": "output data",
                "timeout": 10
            },
            {
                "input": [
                    "input line 1",
                    "input line 2"
                ],
                "output": [
                    "output line 1",
                    "output line 2"
                ],
                "timeout": 15
            },
            {
                "input": [
                    "Alice",
                    "25"
                ],
                "output": [
                    "What is your name?",
                    "Hello, Alice!",
                    "What is your age?",
                    "You are 25 years old."
                ],
                "timeout": 10,
                "interleaved": true
            }
        ]
    }

* `command`: (Optional for compiled languages) The command that will be used to execute the script. It can be a single executable (e.g. "python") or a compound command. For backward compatibility, this is still supported, but `run_command` is preferred for clarity.
* `run_command`: (Optional) Explicitly specifies the command to run the program. Takes precedence over `command` if both are provided.
* `compile_command`: (Optional) Command to compile the source code before running tests. Supports `{source}` and `{output}` placeholders. Required for compiled languages like C, C++, Java, etc.
* `path`: The path to the script file or folder. If it is a folder, all the files inside will be tested.
* `tests`: A list of tests that will be run. There must be at least one test, but there can be many. Each test has the following properties:
  - `input`: The input data for the test. It can be empty, a single entry, or an array of entries.
  - `output`: The expected output data for the test. It can be empty, a single entry, or an array of entries.
  - `timeout`: The timeout for the test in seconds.
  - `interleaved` (optional): Set to `true` for interactive programs that alternate between prompting and waiting for input. Default is `false` for backward compatibility.
  - `unordered` (optional): Set to `true` for non-deterministic output where the order of lines doesn't matter, as long as all expected lines are present. Default is `false`.

Note that input and output can be either empty, a single entry, or an array of entries.

### Multi-Language Support

Testio supports testing programs written in multiple programming languages. You can configure it to work with:
- **Compiled languages** (C, C++, Rust, Go, Java, etc.)
- **Interpreted languages** (Python, JavaScript/Node.js, Ruby, PHP, Perl, etc.)

#### Examples

**C Program:**

    {
        "compile_command": "gcc {source} -o {output}",
        "path": "hello.c",
        "tests": [
            {
                "input": [],
                "output": ["Hello from C!"],
                "timeout": 5
            }
        ]
    }

**C++ Program:**

    {
        "compile_command": "g++ {source} -o {output}",
        "path": "hello.cpp",
        "tests": [
            {
                "input": [],
                "output": ["Hello from C++!"],
                "timeout": 5
            }
        ]
    }

**Java Program:**

    {
        "compile_command": "javac {source}",
        "run_command": "java",
        "path": "Hello.java",
        "tests": [
            {
                "input": [],
                "output": ["Hello from Java!"],
                "timeout": 5
            }
        ]
    }

**Node.js/JavaScript:**

    {
        "run_command": "node",
        "path": "hello.js",
        "tests": [
            {
                "input": [],
                "output": ["Hello from Node.js!"],
                "timeout": 5
            }
        ]
    }

**Ruby:**

    {
        "run_command": "ruby",
        "path": "hello.rb",
        "tests": [
            {
                "input": [],
                "output": ["Hello from Ruby!"],
                "timeout": 5
            }
        ]
    }

**Go:**

    {
        "compile_command": "go build -o {output} {source}",
        "path": "hello.go",
        "tests": [
            {
                "input": [],
                "output": ["Hello from Go!"],
                "timeout": 5
            }
        ]
    }

**Rust:**

    {
        "compile_command": "rustc {source} -o {output}",
        "path": "hello.rs",
        "tests": [
            {
                "input": [],
                "output": ["Hello from Rust!"],
                "timeout": 5
            }
        ]
    }


### Interleaved Input/Output Testing

Testio now supports testing interactive programs that alternate between producing output and waiting for input. This is useful for testing:
- Interactive CLI applications
- Programs that prompt users for information
- Applications that simulate conversations or dialogues
- Any scenario where input/output alternates in a back-and-forth manner

To enable interleaved testing, add `"interleaved": true` to your test configuration. When this flag is set:
- The test runner handles interactive prompts properly
- Inputs are provided in response to program prompts
- All output (including prompts) is captured and compared against expected output

Example of an interactive program test:

    {
        "command": "python3",
        "path": "interactive_program.py",
        "tests": [
            {
                "input": ["Alice", "25", "London"],
                "output": [
                    "What is your name?",
                    "Hello, Alice!",
                    "What is your age?",
                    "You are 25 years old.",
                    "Where are you from?",
                    "Nice to meet you from London!"
                ],
                "timeout": 5,
                "interleaved": true
            }
        ]
    }

### Non-Deterministic Output Testing

Testio supports testing programs with non-deterministic output where lines may appear in any order. This is useful for testing:
- Multi-threaded applications where output order varies
- Programs that process items in parallel
- Any scenario where the output content is predictable but the order is not

To enable unordered testing, add `"unordered": true` to your test configuration. When this flag is set:
- All expected lines must be present in the actual output
- The order of lines does not matter
- Duplicate lines are handled correctly (counts must match)

Example of testing non-deterministic output:

    {
        "command": "python3",
        "path": "parallel_processor.py",
        "tests": [
            {
                "input": "",
                "output": [
                    "Processing item A",
                    "Processing item B",
                    "Processing item C",
                    "All items processed"
                ],
                "timeout": 10,
                "unordered": true
            }
        ]
    }

In this example, the first three lines can appear in any order, as long as all of them are present.


## Architecture

Testio has three main modules: the parser module, the program_runner module, and the output_comparator module.

The parser module parses the config file, which contains the paths to the executables and tests. The config file should be in JSON format and should include the following fields:

* executables_dir: the directory containing the executables to be tested
* tests_dir: the directory containing the tests
* timeout: the maximum time (in seconds) that a program is allowed to run before it is terminated

![Alt text](https://github.com/djeada/Testio/blob/main/resources/diagram.png)

The program_runner module runs the programs and captures their standard output. The output_comparator module compares the actual output to the expected output. If the output is correct, Testio will print a green checkmark. If the output is incorrect, Testio will print a red X. The results are then stored in a dictionary and can be printed to the command line or reported in a PDF document.

## Future Development

There are a few planned features and known issues that are being worked on for Testio:

- [x] Enhanced Timeout Management: The timeout parameter will be changed from a regex-based approach to an array-based approach, providing a more flexible and intuitive way of managing timeouts.
- [x] Improved User Interface: A frontend generated with Flask templates will be added to make the interface more user-friendly and intuitive. This will make it easier for users to interact with Testio and get the results they need.
- [x] Add support for testing applications written in multiple programming languages.

 
## Contributing
We welcome contributions to Testio! If you would like to contribute, please follow these guidelines:

1. Submit a pull request with a clear explanation of your changes
1. Follow the style guide for the project (e.g. PEP8 for Python code)
1. Include test cases for any new features or changes

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
