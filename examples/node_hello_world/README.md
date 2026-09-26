# node_hello_world

Runs `hello.js` with `node` and checks that it prints `Hello from Node.js!`.

## Files
- `hello.js`: Minimal Node.js program under test.
- `config.json`: Uses `run_command: node` and defines 1 no-input test.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Testing JavaScript programs.
- Node (like the JVM) reserves a large virtual address space at startup, so
  Testio does not apply its address-space memory limit to it; CPU time,
  file-size and wall-clock limits still apply. Use container memory limits
  (see the Docker setup) to bound memory for these runtimes.
