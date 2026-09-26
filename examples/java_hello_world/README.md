# java_hello_world

Compiles `Hello.java` with `javac`, then runs the class with `java`.

## Files
- `Hello.java`: Minimal Java program under test.
- `config.json`: `compile_command: javac {source}` and
  `run_command: java -cp {dir} {stem}`. `{dir}` and `{stem}` are the directory
  and name of the compiled `Hello.class`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Placeholders in `run_command` for runtimes that do not take a file path.
- For single-file programs on Java 11+, `"run_command": "java"` with no
  `compile_command` also works (`java Hello.java`).
