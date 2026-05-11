# c_hello_world

Compiles `hello.c` with `gcc` and checks that it prints `Hello from C!`.

## Files
- `hello.c`: Minimal C program under test.
- `config.json`: Uses `gcc {source} -o {output}` and defines 1 no-input test expecting `Hello from C!`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- A minimal C compilation workflow.
- Verifying output for a no-input program.
