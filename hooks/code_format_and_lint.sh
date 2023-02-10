#!/bin/sh

# This hook ensures that the code is formatted and organized correctly.

# Black is used to format the code according to PEP 8 guidelines.
black $1

# Autoflake removes all unused imports and helps to keep the code clean.
autoflake --remove-all-unused-imports -i -r $1

# Isort sorts the imports according to PEP 8 guidelines.
isort $1

# Add additional checks or formatting tools as necessary.
