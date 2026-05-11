# execution_errror

Runs `program.py` with `python3`, expecting `5`, but the program crashes instead of completing successfully.

## Files
- `program.py`: Python program that fails at runtime.
- `config.json`: Runs `python3`, provides no input, and expects output `5` for 1 test.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- How Testio reports execution errors.
- Failure handling for exceptions or other non-zero exits.
