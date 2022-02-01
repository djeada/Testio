# Testio

[![Build Status](https://travis-ci.org/djeada/testio.svg?branch=main)](https://travis-ci.org/djeada/testio)
<a href="https://github.com/djeada/testio/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/djeada/testio"></a>
<a href="https://github.com/djeada/testio/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/djeada/testio"></a>
<a href="https://github.com/djeada/testio/blob/master/LICENSE.txt"><img alt="GitHub license" src="https://img.shields.io/github/license/djeada/testio"></a>
<a href=""><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

<img src="https://github.com/djeada/Testio/blob/main/resources/logo.png" alt="Testio" width="200"/>

Testio is a lightweight framework designed for testing applications' standard output. 

## Purpose

The aim of this project is to provide a simple and easy way to test your application's standard output. It is specifically targeted at highschool teachers and college instructors. If your students were assigned to write a program that for a given set of inputs is expected to produce an output, then this project is for you. Instead of testing each program individually, you can simply specify a directory containing all the programs, as well as a set of inputs and expected outputs. Testio will then run each program and compare the output to the expected output. If the output is correct, Testio will print a green checkmark. If the output is incorrect, Testio will print a red X. Additionally for each program, a pdf report will be generated containing the results of the tests.

## Requirements

* Python 3.8


## Design 

![Alt text](https://github.com/djeada/Testio/blob/main/resources/diagram.png)


## TODO

- [-] Change the timeout parameter from regex based to array.
- [-] Add frontend generated with Flask templates.
- [-] Create a desktop app with a browser that can run the Flask app using the QT framework. 
