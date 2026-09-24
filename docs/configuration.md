# Test suite configuration

A Testio test suite is a JSON file. The formal definition is
[`src/testio/schemas/testio-config.schema.json`](../src/testio/schemas/testio-config.schema.json);
editors that understand JSON Schema will autocomplete and validate it if you add

```json
{ "$schema": "https://raw.githubusercontent.com/djeada/Testio/main/src/testio/schemas/testio-config.schema.json" }
```

Check a file without running anything:

```bash
testio validate config.json            # structural errors -> exit code 1
testio validate config.json --strict   # also warn about risky timeouts etc.
```

## Top-level fields

| Field | Required | Meaning |
|---|---|---|
| `path` | yes | Program to test, relative to the config file. If it is a directory, every file in it is tested separately (one result per student/program). |
| `tests` | yes | List of test cases (see below). |
| `command` | one of the three | Interpreter to run the program with; the program path is appended: `"python3"` runs `python3 <path>`. |
| `run_command` | one of the three | Same as `command` and takes precedence over it. |
| `compile_command` | one of the three | Build step run before testing. `{source}` is replaced by the source file name, `{output}` by the path of the produced binary, e.g. `"gcc {source} -o {output}"`. With no `run_command`, the compiled binary is executed directly. |

Commands are split like a shell would split them but are **not** run through a
shell: pipes, redirections and `$VARS` have no effect. The executable must be
one of `python`, `python3`, `node`, `ruby`, `perl`, `java`, `javac`, `go`,
`gcc`, `g++`, `clang`, `rustc` (by name or absolute path), or a local
`./program`. Add more with `TESTIO_ALLOWED_EXECUTABLES=bash,php`.

## Test cases

| Field | Default | Meaning |
|---|---|---|
| `input` | required | Standard input. Either a list of lines (`["5", "3"]`) or one string (`"5\n3"`). |
| `output` | required | Expected standard output, same format as `input`. |
| `timeout` | `5` | Wall-clock limit in seconds (max `TESTIO_MAX_TEST_TIMEOUT`, default 300). |
| `use_regex` | `false` | `output` is a regular expression that must match the **entire** output. |
| `unordered` | `false` | Compare lines as a multiset: order and blank lines are ignored, duplicates count. |
| `interleaved` | `false` | For programs that prompt and read repeatedly. Input lines are supplied in order. |

## How a result is decided

Each test ends in exactly one state:

| Result | When |
|---|---|
| `MATCH` | The program exited with status 0 and its output matched. |
| `MISMATCH` | The program exited with status 0 but the output differed. |
| `EXECUTION_ERROR` | Compilation failed, the program exited non-zero or was killed by a signal (e.g. a segfault), it printed more than the output limit, or it could not be started. |
| `TIMEOUT` | The program ran longer than `timeout`. |

Comparison details:

* Trailing newlines at the end of the output are ignored on both sides; all
  other whitespace is significant.
* `\r` characters are removed, so Windows line endings compare equal.
* Anything written to standard error is shown in the report but does not fail
  a test by itself. Warnings are fine; a non-zero exit status is not.
* Output that is not valid UTF-8 is decoded with replacement characters
  instead of crashing the run.

## Exit status of `testio run`

| Status | Meaning |
|---|---|
| `0` | Every test passed. |
| `1` | At least one test failed, or the config/program could not be loaded. |
| `2` | Invalid command-line usage. |

This makes `testio run` usable directly as a CI step.

## Example: C program with compilation

```json
{
  "compile_command": "gcc {source} -o {output}",
  "path": "calculator.c",
  "tests": [
    { "input": ["2", "3"], "output": ["5"] },
    { "input": ["10", "-4"], "output": ["6"], "timeout": 2 }
  ]
}
```

More complete examples live in [`examples/`](../examples); each one's
README states the result it is expected to produce, and the test suite
checks every one of them.
