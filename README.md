# Testio

[![Build Status](https://travis-ci.org/djeada/testio.svg?branch=main)](https://travis-ci.org/djeada/testio)
<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

<img src="https://github.com/djeada/Testio/blob/main/resources/logo.png" alt="Testio" width="200"/>

Testio is a lightweight framework for testing the standard output of applications.

## Purpose

The aim of this project is to provide a simple and easy way to test your application's standard output. It is specifically targeted at highschool teachers and college instructors. If your students were assigned to write a program that for a given set of inputs is expected to produce an output, then this project is for you. Instead of testing each program individually, you can simply specify a directory containing all the programs, as well as a set of inputs and expected outputs. Testio will then run each program and compare the output to the expected output. If the output is correct, Testio will print a green checkmark. If the output is incorrect, Testio will print a red X. Additionally for each program, a pdf report will be generated containing the results of the tests.

Another use case for Testio is implementation of end-to-end tests in CI/CD pipelines. If you are using scripts or compiling executables, you can use Testio to test the output of your program for the given set of inputs. If single test fails, testio will exit with a non-zero exit code. If all tests pass, testio will exit with a zero exit code. 

## Requirements

* Python 3.8


## Installation

There are two ways to install Testio. One is to install the project using virtualenv. The other way is to install the project using poetry. Both will create a virtual environment in which you can keep your project's dependencies.

## From virtualenv

    $ git clone https://github.com/djeada/Testio.git
    $ cd Testio
    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt

### From poetry

    $ git clone https://github.com/djeada/Testio.git
    $ cd Testio
    $ poetry shell
    $ poetry update

### Starting the CLI application

    $ src/main_command_line.py path/to/config_file.json

### Starting the Flask server

    $ src/flask_app/flask_app.py

### Starting the GUI application

    $ src/qt_app/qt_app.py

## Design 

The application is divided into three separate interface:

* The command line interface
* The flask server
* The Qt application

Each part is implemented in a different file. The command line interface is implemented in the main_command_line.py file. The flask server is implemented in the flask_app.py file. The Qt application is implemented in the qt_app.py file.

### Command line interface

Backend scripts are located in the src/testio_core folder. The three main modules are:

* parser
* program_runner
* output_comparator

 First the config file containing paths to executables and tests consiting of inputs and expected outputs is parsed. Then the programs are run and the actual output is compared to the expected output. The results are stored in a dictionary. The results are then printed to the command line. There is also an option to generate a pdf report containing the results.

![Alt text](https://github.com/djeada/Testio/blob/main/resources/diagram.png)

### Flask server

The purpose of the flask server is to provide a web interface for the command line interface. The flask server is implemented in the flask_app.py file.

### Qt application

The purpose of the Qt application is to embed the flask application in a desktop GUI. The Qt application is implemented in the qt_app.py file.

## TODO

- [-] Change the timeout parameter from regex based to array.
- [-] Create the basic documentation structure.
- [-] Add frontend generated with Flask templates.
- [-] Create a desktop app with a browser that can run the Flask app using the QT framework. 
