# Testio

[![CI](https://github.com/djeada/Testio/actions/workflows/python-app.yml/badge.svg)](https://github.com/djeada/Testio/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/github/license/djeada/testio)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

Testio runs programs against **input → expected output** test suites. Use it to
grade student submissions in bulk, run an exam or homework through a web UI,
or gate a CI pipeline on the observable behaviour of a command-line program.

![testio](https://github.com/djeada/Testio/assets/37275728/ab799306-e5b3-457c-bb69-0a4322ee6ad2)

- **Any language**: Python, C, C++, Java, JavaScript, Ruby, Go, Rust… with an optional compile step.
- **Honest results**: a test passes only if the program exits cleanly *and* its output matches. Crashes, segfaults, timeouts, output floods and compile errors are all reported as failures.
- **Flexible matching**: exact, regular expression, or order-insensitive.
- **CI friendly**: non-zero exit code on failure; JSON, JUnit XML and TAP reports.
- **Classroom tooling**: batch grading with CSV/HTML/JSON reports, printable problem sheets, assignment scaffolding, student self-check, and a web UI for homework and exams.

## Install

Requires Python 3.10+ on Linux or macOS, plus the compilers/interpreters for the
languages you test.

```bash
pip install git+https://github.com/djeada/Testio.git
# or, from a checkout:
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

This installs two commands, `testio` (CLI) and `testio-server` (web UI).
From a source checkout without installing, `python src/main.py cli …` and
`python src/main.py fastapi …` are equivalent.

## Quick start

```bash
cat > hello.py <<'EOF'
name = input()
print(f"Hello, {name}!")
EOF

cat > config.json <<'EOF'
{
  "command": "python3",
  "path": "hello.py",
  "tests": [
    { "input": ["Ada"], "output": ["Hello, Ada!"] },
    { "input": ["Linus"], "output": ["Hello, Linus!"], "timeout": 2 }
  ]
}
EOF

testio run config.json      # exit code 0 = all passed, 1 = failures
```

The full config format (compiled languages, regex and unordered matching,
interactive programs, how pass/fail is decided) is in
**[docs/configuration.md](docs/configuration.md)**. Every directory in
[`examples/`](examples) is a runnable suite whose README states its expected
result.

## CLI

| Command | What it does |
|---|---|
| `testio run config.json` | Run a suite. `-q` summary only, `-f json\|junitxml\|tap` machine-readable output, `-o FILE` write a report. |
| `testio validate config.json…` | Check configs without running them (`--strict` for best-practice warnings, `--fix` to normalise). |
| `testio batch config.json submissions/` | Grade every file in a directory; `-f csv\|html\|json\|text`, `-o FILE`, `--parallel N`. |
| `testio export config.json -f html\|md\|pdf\|all` | Printable problem sheet; `--include-solutions` for the teacher copy. PDF needs `pip install 'testio[pdf]'`. |
| `testio generate config.json -t python\|c\|java…` | Create a config template (interactive unless `-n`). |
| `testio init homework1 -t homework\|exam\|lab -l python` | Scaffold an assignment directory. |
| `testio student test solution.py config.json` | Student self-check with friendly output (`check`, `practice` also available). |

In CI:

```yaml
- run: pip install git+https://github.com/djeada/Testio.git
- run: testio run tests/config.json -f junitxml -o testio.xml
```

## Web UI

```bash
export TESTIO_TEACHER_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
testio-server --mode teacher --host 127.0.0.1 --port 5000
testio-server --mode student --host 0.0.0.0 --port 5001   # separate student-facing instance
```

Teacher mode has the config generator, homework grading and exam management;
student mode only has the submission workspace and exams. API docs are served
at `/docs`. Deployment, authentication and all environment variables are
covered in **[docs/deployment.md](docs/deployment.md)**.

### Docker

```bash
export TESTIO_TEACHER_API_KEY=change-me
docker compose up -d        # http://localhost:8000
```

The image includes gcc/g++, Node.js and Ruby (`--build-arg INSTALL_JAVA=true`
adds a JDK), runs as an unprivileged user, and the compose file bounds the
container's memory, CPU and process count.

## Security

Testio executes the code it is given. Resource limits, a scrubbed
environment and an executable allow-list reduce the blast radius, but they
are not a sandbox. **Run servers that accept untrusted submissions inside a
container** (the provided Docker setup) and set a teacher API key. See
[SECURITY.md](SECURITY.md) for the threat model and how to report issues.

## How it works

```
config.json ─► ConfigParser ─► ExecutionManagerFactory ─┬─► compile (optional)
                (validation)     (one entry per program) │
                                                          ▼
                              run_process (rlimits, timeout, output cap,
                              process-group kill, clean env) per test
                                                          ▼
                              OutputComparator ─► MATCH / MISMATCH /
                                                  EXECUTION_ERROR / TIMEOUT
                                                          ▼
                              CLI renderer · JSON/JUnit/TAP · web UI
```

Code lives in `src/testio`: `core/` is the engine (parsing, compiling,
running, comparing), `apps/cli` and `apps/server` are the two front ends.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: `make install`, then
`make check` (lint + tests) before opening a pull request.

## License

[MIT](LICENSE)
