# no_input

Runs `program.py` with no stdin and checks that it prints `xz`.

## Files
- `program.py`: Python program under test.
- `config.json`: Uses `python3` for 1 test with no input and expected output `xz`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Testing a program that does not read input.
- Simple output verification for no-input scripts.
