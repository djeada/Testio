# multiple_tests

Runs `program.py` against three different passing test cases using the same `python3` command.

## Files
- `program.py`: Python program under test.
- `config.json`: Uses `python3` and defines 3 passing cases: `(2,10)->(12,20)`, `(-5,7)->(2,-35)`, `(0,0)->(0,0)`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Running multiple test cases against one program.
- Checking different inputs while reusing one config file.
