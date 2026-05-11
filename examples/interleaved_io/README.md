# interleaved_io

Runs an interactive `program.py` session that prompts for a name, age, and city with interleaved I/O enabled.

## Files
- `program.py`: Interactive Python program under test.
- `config.json`: Uses `python3`, sets `interleaved: true`, and checks the full prompt/response conversation for 1 test.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Testing prompts mixed with user input.
- Interleaved I/O verification for interactive programs.
