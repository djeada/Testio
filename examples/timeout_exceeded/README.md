# timeout_exceeded

Runs `program.py` with a `0.1` second limit, so the program exceeds the timeout before producing the expected output.

## Files
- `program.py`: Python program that runs too long.
- `config.json`: Uses `python3`, sets `timeout` to `0.1`, provides no input, and expects output `6`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- How Testio handles timeout failures.
- Enforcing per-test execution time limits.
