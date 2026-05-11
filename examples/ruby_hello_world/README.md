# ruby_hello_world

Runs `hello.rb` with `ruby` and checks that it prints `Hello from Ruby!`.

## Files
- `hello.rb`: Minimal Ruby program under test.
- `config.json`: Uses `run_command: ruby` and defines 1 no-input test expecting `Hello from Ruby!`.

## Run
From inside this directory, run:
```bash
testio run config.json
```

## What this demonstrates
- Using Testio with a non-Python language.
- Configuring execution with `run_command`.
