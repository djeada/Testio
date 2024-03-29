#!/usr/bin/env bash

paths=(src tests examples)  # If you wish to check more directories, you may add them to this list.

for path in "${paths[@]}"; do
  python hooks/remove_carriage_return.py "$path"
  hooks/code_format_and_lint.sh "$path"
done
