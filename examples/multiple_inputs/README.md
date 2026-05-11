# multiple_inputs

Runs `program.py` with two stdin lines in one test and checks that it prints the sum and product.

## Files
- `program.py`: Python program that reads two values.
- `config.json`: Uses `python3` for 1 test with inputs `2` and `10`, expecting outputs `12` and `20`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Feeding multiple input lines through stdin.
- Validating multi-line output from a single test.
