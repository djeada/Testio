# multiple_programs_tested

Points Testio at a `scripts/` directory so every program inside it is tested with the same configuration.

## Files
- `scripts/`: Directory containing `main_a.py`, `main_b.py`, `main_c.py`, `main_d.py`, and `main_e.py`.
- `config.json`: Uses `python3`, targets `scripts`, and applies 1 test with inputs `2` and `10` expecting `12` and `20`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Testing all files in a directory at once.
- Reusing one test definition across multiple programs.
