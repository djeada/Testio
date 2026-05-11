# failed_test

Runs `program.py` with three add/multiply cases where the last expected result is intentionally wrong.

## Files
- `program.py`: Python program under test.
- `config.json`: Uses `python3` for 3 tests; the final case expects `0` and `1` even though the program returns `0` and `0`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- What a failing test case looks like.
- How mismatched expected and actual output is reported.
