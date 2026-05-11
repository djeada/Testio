# c_calculator

Compiles `calculator.c` with `gcc` and runs three add/multiply test cases.

## Files
- `calculator.c`: C program under test.
- `config.json`: Uses `gcc {source} -o {output}` and defines 3 tests: `(5,3)->(8,15)`, `(10,2)->(12,20)`, `(0,0)->(0,0)`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Compiling C code before execution.
- Running a multi-test suite against one program.
