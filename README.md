# Testio

[![Build Status](https://travis-ci.org/djeada/testio.svg?branch=main)](https://travis-ci.org/djeada/testio)
<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

Testio is a flexible and powerful testing framework that uses multiprocessing to verify the standard output of applications. With its three convenient interfaces: CLI, web server, and GUI, you can test applications with a variety of configurations and inputs on a large scale.

![testio](https://user-images.githubusercontent.com/37275728/213671290-98a831ab-3999-4246-ba54-3ccd476d57b5.png)

## Overview
Testio is a tool that was created to make testing the standard output of applications effortless and efficient. Its user-friendly design makes it a valuable tool for teachers, who can use it to assess the programs submitted by their students and ensure they meet the intended requirements.

As a teacher, you can utilize Testio to automate the evaluation process of homework tasks and exams. By providing a set of inputs, the tool will execute the programs or scripts submitted by students and compare the results to the expected output. Testio will then generate a report for the teacher, providing a clear and concise assessment of each program's functionality.

In addition to its educational benefits, Testio is also a useful tool for industry professionals in CI/CD pipelines. By running end-to-end tests on an application, you can use Testio to verify that it operates as intended. Whether you are testing scripts or compiling executables, the tool can help you validate the output of your program for a given set of inputs. If a test fails, Testio will exit with a non-zero exit code, signaling that the application needs attention. If all tests pass, the tool will exit with a zero exit code, indicating that the application is working as expected.

## Key Features
- Easy and efficient testing of application outputs
- Three user-friendly interfaces: CLI, WEB SERVER, and GUI
- Ideal for teachers to check student programs and homework assignments
- Can be integrated into CI/CD pipelines in the industry
- Compares application output against expected output
- Option to generate a PDF report of results
- Flask API for easy integration with other tools

## Requirements

* Python 3.8+
* flask
* pyqt6

## Installation

The easiest way to install Testio is to use virtualenv:


    $ git clone https://github.com/djeada/Testio.git
    $ cd Testio
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt

## Usage

Testio provides three different interfaces for running tests: a command-line interface (CLI), a web interface using a Flask server, and a desktop graphical user interface (GUI) using Qt. All three interfaces provide the similar functionality, but allow you to interact with Testio in different ways.

### Command-line interface

To use the CLI, run the main.py script with the cli argument and pass the path to the config file as an argument:

    $ python src/main.py cli path/to/config_file.json

The CLI will run the tests specified in the config file and display the results on the command line. You can also generate a PDF report containing the results by passing the --report flag:

    $ python src/main.py cli path/to/config_file.json --report

### Flask server

To use the web interface, run the main.py script with the flask argument:

    $ python src/main.py flask

This will start the Flask server and serve the web interface at http://localhost:5000. You can specify the path to the config file using the --config flag:

    $ python src/main.py flask --config path/to/config_file.json

To update the test suite, use the following API endpoint:

    curl -X POST \
    --header "Content-Type: application/json" \
    -d @/path/to/file.json \
    http://localhost:5000/update_test_suite

### Desktop GUI

To use the desktop GUI, run the main.py script with the gui argument:

    $ python src/main.py gui

This will start the Qt application and display the GUI. You can specify the path to the config file using the --config flag:

    $ python src/main.py gui --config path/to/config_file.json

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
            }
        ]
    }

* `command`: The command that will be used to execute the script. It can be a single executable (e.g. "python") or a compound command (e.g. "python path/to/script.py"). If you want to test an executable, you can leave this entry empty.
* `path`: The path to the script file or folder. If it is a folder, all the files inside will be tested.
* `tests`: A list of tests that will be run. There must be at least one test, but there can be many. Each test has the following properties:
  - `input`: The input data for the test. It can be empty, a single entry, or an array of entries.
  - `output`: The expected output data for the test. It can be empty, a single entry, or an array of entries.
  - `timeout`: The timeout for the test in seconds.

Note that input and output can be either empty, a single entry, or an array of entries. 


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
- [x] Desktop App: A desktop app will be created using the QT framework, which will allow users to run the Flask app in a browser-like environment. 
- [ ] Add support for testing applications written in multiple programming languages.
 
## Contributing
We welcome contributions to Testio! If you would like to contribute, please follow these guidelines:

1. Submit a pull request with a clear explanation of your changes
1. Follow the style guide for the project (e.g. PEP8 for Python code)
1. Include test cases for any new features or changes

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
