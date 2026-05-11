#!/usr/bin/env bash
# Manual hook runner.
#
# NOTE: Formatting and linting are now also handled by pre-commit (see
# .pre-commit-config.yaml).  This script is kept for environments where
# pre-commit is not installed and for CI steps that need explicit path-scoped
# runs (e.g. auditing a single directory).
#
# To install pre-commit hooks instead:
#   pip install pre-commit && pre-commit install

paths=(src tests examples)  # If you wish to check more directories, you may add them to this list.

for path in "${paths[@]}"; do
  python hooks/remove_carriage_return.py "$path"
  hooks/code_format_and_lint.sh "$path"
done
