# Testio

[![Build Status](https://travis-ci.org/djeada/testio.svg?branch=main)](https://travis-ci.org/djeada/testio)
<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

Testio is a simple and efficient testing framework that uses multiprocessing to verify the standard output of applications. With Testio, you can quickly and easily write tests to ensure that your applications are functioning as expected. Whether you are a software developer looking to improve the quality of your code or a student learning about testing techniques, Testio is a valuable tool for your toolkit.

![testio](https://user-images.githubusercontent.com/37275728/213671290-98a831ab-3999-4246-ba54-3ccd476d57b5.png)

## Overview

Testio was designed to provide an easy and efficient way to test the standard output of applications. It is particularly useful for teachers, who can use it to check programs submitted by their students and make sure they are working as intended.

To use the tool for this purpose, teachers can specify a directory with all the programs to be tested, along with a set of inputs and expected outputs for each program. The tool will then run each program and compare the output to the expected output. If the output is correct, it will print a green checkmark. If the output is incorrect, it will print a red X. Additionally, for each program, the tool can generate a PDF report with the test results.

In addition to being helpful for teachers, Testio can also be used in the industry in CI/CD pipelines. In this context, it can be used to perform end-to-end tests on an application to ensure it behaves as expected. For example, if you are using scripts or compiling executables, you can use the tool to test the output of your program for a given set of inputs. If a single test fails, the tool will exit with a non-zero exit code. If all tests pass, it will exit with a zero exit code, indicating that the application is functioning as expected.

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

Testio provides three different interfaces for running tests: a command-line interface (CLI), a web interface using a Flask server, and a desktop graphical user interface (GUI) using Qt. All three interfaces provide the same functionality, but allow you to interact with Testio in different ways.

### Command-line interface

To use the CLI, run the main_command_line.py script and pass the path to the config file as an argument:

    $ src/main_command_line.py path/to/config_file.json

The CLI will run the tests specified in the config file and display the results on the command line. You can also generate a PDF report containing the results by passing the --report flag:

    $ src/main_command_line.py path/to/config_file.json --report

### Flask server

To use the web interface, run the flask_app.py script:

    $ src/flask_app/flask_app.py

This will start the Flask server and serve the web interface at http://localhost:5000. You can specify the path to the config file using the --config flag:

    $ src/flask_app/flask_app.py --config path/to/config_file.json


To update the test suite, use the following API endpoint:

    curl -X POST \
    --header "Content-Type: application/json" \
    -d @/path/to/file.json \
    http://localhost:5000/update_test_suite


### Desktop GUI

To use the desktop GUI, run the qt_app.py script:

    $ src/qt_app/qt_app.py

This will start the Qt application and display the GUI. You can specify the path to the config file using the --config flag:

    $ src/qt_app/qt_app.py --config path/to/config_file.json

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

- [x] Change the timeout parameter from regex based to array.
- [x] Add frontend generated with Flask templates.
- [ ] Create a desktop app with a browser that can run the Flask app using the QT framework. 

## Contributing
We welcome contributions to Testio! If you would like to contribute, please follow these guidelines:

1. Submit a pull request with a clear explanation of your changes
1. Follow the style guide for the project (e.g. PEP8 for Python code)
1. Include test cases for any new features or changes

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
