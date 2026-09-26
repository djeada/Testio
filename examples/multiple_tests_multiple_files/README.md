# multiple_tests_multiple_files

Runs the same three tests against every program in `scripts/`.

## Files
- `scripts/`: `main_a.py` … `main_e.py`, one program per student.
- `config.json`: Uses `python3`, targets `scripts`, and defines 3 tests that
  read two numbers and print their sum and product.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## Expected result
Not every program is correct, so the run reports failures and exits with a
non-zero status. Use `testio batch config.json scripts/` for a per-student
score table instead.
