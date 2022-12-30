# Testio

[![Build Status](https://travis-ci.org/djeada/testio.svg?branch=main)](https://travis-ci.org/djeada/testio)
<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

<img src="https://github.com/djeada/Testio/blob/main/resources/logo.png" alt="Testio" width="200"/>

Testio is a simple and efficient testing framework that uses multiprocessing to verify the standard output of applications. With Testio, you can quickly and easily write tests to ensure that your applications are functioning as expected. Whether you are a software developer looking to improve the quality of your code or a student learning about testing techniques, Testio is a valuable tool for your toolkit.

## Overview

Testio allows you to test the standard output of applications by specifying a directory containing the programs to be tested, as well as a set of inputs and expected outputs. Testio is implemented in Python and is divided into three separate interfaces: a command-line interface, a Flask server, and a Qt application. The command-line interface allows you to run tests and generate reports from the command line, the Flask server provides a web interface for running tests, and the Qt application embeds the Flask application in a desktop GUI.

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

### Desktop GUI

To use the desktop GUI, run the qt_app.py script:

    $ src/qt_app/qt_app.py

This will start the Qt application and display the GUI. You can specify the path to the config file using the --config flag:

    $ src/qt_app/qt_app.py --config path/to/config_file.json


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

- [-] Change the timeout parameter from regex based to array.
- [-] Add frontend generated with Flask templates.
- [-] Create a desktop app with a browser that can run the Flask app using the QT framework. 

## Contributing
We welcome contributions to Testio! If you would like to contribute, please follow these guidelines:

1. Submit a pull request with a clear explanation of your changes
1. Follow the style guide for the project (e.g. PEP8 for Python code)
1. Include test cases for any new features or changes

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
