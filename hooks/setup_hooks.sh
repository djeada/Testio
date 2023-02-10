#!/bin/bash

# This script sets up a pre-commit Git hook for your Python project.

# Check if a pre-commit file already exists.
if [ -f .git/hooks/pre-commit ]; then
  echo "A pre-commit hook already exists. Backing it up to pre-commit.bak"
  mv .git/hooks/pre-commit .git/hooks/pre-commit.bak
fi

# Create a new pre-commit file.
echo "#!/bin/sh

# This is the Git pre-commit hook.

# Run the code format and linting script.
hooks/run_all.sh

# Check the exit status of the above script.
if [ \$? -ne 0 ]; then
  echo 'Code format and linting errors found. Commit failed.'
  exit 1
fi

# Continue with the commit if the above script passed.
exit 0" > .git/hooks/pre-commit

# Make the pre-commit file executable.
chmod +x .git/hooks/pre-commit

# Confirm that the pre-commit hook has been set up.
echo "Git pre-commit hook has been set up successfully."
