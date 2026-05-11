# interleaved_io_complex

Runs an interactive calculator with interleaved prompts and three different operation tests.

## Files
- `calculator.py`: Interactive calculator program.
- `config.json`: Uses `python3`, sets `interleaved: true`, and defines 3 calculator sessions that end with `15.0`, `60.0`, and `25.0`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Complex interleaved I/O with multiple prompts.
- Reusing one interactive program across several tests.
