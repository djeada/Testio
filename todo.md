# Testio – Improvement, Expansion & Refactor TODO

A thorough review of the repository revealed numerous bugs, design flaws,
security risks, dead code, packaging gaps, and missing functionality.
Items are grouped by area and (roughly) by severity.
Use the status markers `[ ] / [~] / [x]` and `(SEV: critical|high|med|low)`
to drive an iterative cleanup.

---

## 0. Top-priority correctness & security issues

- [~] **(SEV: critical)** Sandbox student code execution.
  `src/core/execution/runner.py`, `interactive_runner.py`, `compiler.py`,
  and the server endpoints execute arbitrary user-supplied code with
  `shell=True`, no resource limits, no namespace isolation, no filesystem
  jail, and no network restrictions. This is dangerous for any deployment
  that accepts external submissions (homework, exam, batch, student
  routes). Introduce one of: Docker per-run container, `nsjail`/`firejail`,
  `bubblewrap`, gVisor, or at minimum POSIX `setrlimit` (RLIMIT_CPU,
  RLIMIT_AS, RLIMIT_NOFILE) plus seccomp filters.
- [x] **(SEV: critical)** Replace `shell=True` everywhere user input can
  reach the command line. `runner.execute_program`, `interactive_runner`,
  and `compiler.compile` should use list-form `subprocess.Popen([...])`
  with `shlex.split` only on a strictly validated command template.
- [x] **(SEV: critical)** `validate_command` in `src/apps/server/validation.py`
  is defined but never called and silently allows anything outside the
  allow-list. Either enforce the allow-list (and call it everywhere a
  user-supplied `command` is parsed: `batch_execution`, `exam_session`,
  `update_test_suite`, `homework_submission`) or remove the function.
- [x] **(SEV: critical)** Add authentication & authorization to the FastAPI
  app. Currently *every* exam-management endpoint is open to the world:
  `POST /api/exam/create_session`, `POST /api/exam/end_session/{id}`,
  `GET /api/exam/submissions/{id}`, `GET /api/export/...`,
  `POST /update_test_suite`, `POST /api/metrics/reset`,
  `POST /homework_submission`. Add role-based auth (teacher vs student)
  with API keys / JWT / session cookies.
- [x] **(SEV: critical)** Insecure CORS configuration in
  `src/apps/server/app/testio_server.py`: `allow_origins=["*"]` combined
  with `allow_credentials=True` is rejected by browsers and unsafe.
  Make origins configurable via env var; default to `[]` or a strict list.
- [x] **(SEV: high)** `src/apps/server/routes/execute_tests.py` overwrites
  the original program file on disk with `Path(path).write_text(script_text)`
  inside `process_file_for_server`. Concurrent requests will corrupt files
  and clobber the source under test. Use a tempdir per request.
- [x] **(SEV: high)** Result strings compared with the literal
  `'ComparisonResult.MATCH'` in `homework_submission.py`, `exam_session.py`,
  `export.py`, and `static/js/*.js`. Relying on `str(Enum)` is brittle.
  Add a stable string field (`result_name`) to `ComparisonOutputData.to_dict`
  and update every consumer + JS templates.
- [x] **(SEV: high)** `Database` singleton in
  `src/apps/server/database/database.py` is unsafe: `ExamSessionsTable`
  calls `__enter__` in its `__init__` and `__exit__` in `close`, so
  *any* caller closing the DB closes it for everyone (and a second route
  handler will silently re-open it without the previously cached cursor).
  Replace with `ConnectionPool` (already implemented but unused) and
  remove the singleton hack.
- [x] **(SEV: high)** `Runner.execute_program` (`src/core/execution/runner.py`)
  contains broken control flow on timeout:
  `queue.get() and queue.put(ExecutionOutputData(timeout=True))` —
  unreadable, also leaks the child process (no `pipe.kill()` / `pipe.wait()`).
  Rewrite using `subprocess.run(..., timeout=...)` with proper
  `TimeoutExpired` cleanup, or use `process.kill(); process.wait()`.
- [x] **(SEV: high)** `Runner.execute_program` strips the last character of
  stdout unconditionally (`[:-1]`). If the program does not end with `\n`,
  real output bytes are lost. Use `rstrip("\n")` (and document the
  contract).
- [x] **(SEV: high)** Compiled artifacts produced by `Compiler.compile`
  are never cleaned up. Long-lived servers will accumulate executables in
  the source tree.
- [x] **(SEV: high)** `tempfile.NamedTemporaryFile(mode='w', suffix='.py')`
  is hard-coded in `homework_submission.py`, `batch_execution.py`,
  `exam_session.py`. Non-Python languages cannot be tested through these
  endpoints. Derive the suffix from the config (or compile_command).

---

## 1. Architecture & refactoring

- [x] **Packaging** — add `pyproject.toml` (PEP 621) with `setuptools` or
  `hatch`, define `testio` console scripts (`testio`, `testio-server`),
  proper package metadata, and remove every `sys.path.append(".")` (24
  occurrences across `src/`). The current import scheme breaks editable
  installs and IDE tooling.
- [x] **Single CLI entry point** — `src/main.py` dispatches between
  `cli` and `fastapi` via positional arg. With `pyproject.toml` console
  scripts, expose `testio` and `testio-server` directly.
- [x] **Deduplicate `process_file`** — implemented twice (in
  `src/apps/cli/main.py` and `src/apps/cli/commands/run.py`). Remove the
  legacy copy.
- [x] **Deduplicate factory methods** — the `# TODO` in
  `src/core/execution/data.py` correctly notes that
  `from_test_suite_config_server` is unnecessary; consolidate with
  `from_test_suite_config_local`.
- [x] **Stop calling private API** — `_create_execution_manager_data`
  (underscore-prefixed) is invoked from `homework_submission.py`,
  `batch_execution.py`, `exam_session.py`, `student.py`. Promote it to a
  public method (or refactor the factory).
- [x] **Use the `ConnectionPool` you already wrote** — `connection_pool.py`
  is fully implemented (~400 LOC) but referenced only by the metrics
  endpoint. Migrate `Database`, `ExamSessionsTable`, `ExecutionManagerDataTable`
  to use it; delete the singleton.
- [x] **Use the `ExecutionQueue` you already wrote** — `queue.py` (~430
  LOC) is dead code outside metrics. Either route all test executions
  through it (so resource limits/priority actually take effect) or delete it.
- [x] **Use the `MemoryCache` decorator** — `cache_result` is implemented
  but not applied. Cache `parse_config_data`, `get_session`, etc.
- [x] **Replace `test.db` / `testio.db` magic strings** — sprinkled across
  `configuration_data.py`, `exam_sessions.py`, and `testio_server.py`.
  Centralize in a `Settings` (pydantic-settings) module driven by env vars.
- [~] **Configuration management** — introduce `pydantic-settings` for
  host, port, DB path, allowed CORS origins, rate-limit values, sandbox
  config, etc. Today these are scattered constants in source files.
- [x] **Remove the `src/apps/server/old/` directory** — legacy templates
  and static assets are still shipped.
- [x] **Logging** — `RequestLoggingMiddleware` calls `logging.basicConfig`
  at import time, which clobbers user logging config. Move to a single
  `src/core/logging.py` initializer called from app factories.
- [x] **Result enum mapping** — extract a single helper
  `result_passed(result_dict_or_obj) -> bool` and use it everywhere
  (currently re-implemented in 6+ places).
- [x] **Split runtime vs. dev requirements** — `requirements.txt` mixes
  `pytest`, `isort`, `autoflake`, `black`, `httpx`. Split into
  `requirements.txt` / `requirements-dev.txt` (or `[project.optional-dependencies]`).
- [~] **Dependency hygiene** — many deps are over-specified or stale:
  `urllib3==1.26.14`, `certifi==2022.12.7`, `requests==2.28.2`,
  `pytest==7.2.1`, `attrs==22.2.0`, `MarkupSafe==2.1.2`,
  `idna==3.4`, `click==8.1.3`. Pin only direct deps; let pip resolve
  transitives. Bump for security patches (CVEs in old urllib3/requests/certifi).
- [x] **`requests`** isn't used anywhere in `src/`; remove from runtime deps.
- [x] **Python version mismatch** — README claims Python 3.8+ but the
  code uses PEP 604 unions (`List[Dict] | None` in `export.py`, line 94)
  which require Python 3.10+. Pick a baseline (recommend 3.10+) and
  enforce in `pyproject.toml` (`requires-python = ">=3.10"`).

---

## 2. Bugs & defects (functional)

- [x] `process_file_for_server` (in `execute_tests.py`) divides by zero
  when `num_tests == 0` (`ratio = passed_tests / num_tests * 100`).
- [x] `from_test_suite_config_server` does not resolve `path` relative to
  the server's working directory; if a relative path is supplied it
  silently breaks.
- [x] `Compiler.compile` uses only the source filename when running
  `gcc/g++/javac/...`, but Java's `javac Foo.java` produces `Foo.class`,
  not the same stem; the returned `output_path` (`source_path_obj.parent /
  source_path_obj.stem`) is wrong for Java/Rust crates/Go modules.
- [x] `Compiler.compile` raises `CompilationError` with `(stderr, returncode)`
  but in the timeout branch it passes `(message, -1)` — `__init__`
  expects `stderr: str, returncode: int`; signature works by accident,
  but the message is awkward.
- [x] `ExecutionManager.run` joins inputs/outputs with `\n` even when the
  test is `interleaved`, then passes the same joined `data_input` into
  `ComparisonInputData.input` *and* sends the list to `InteractiveRunner`.
  Inputs are double-handled.
- [x] `OutputComparator._compare_unordered` uses sorted-list equality
  *and* enforces equal length. The README/docstring says "Duplicate
  lines are handled correctly (counts must match)" — this is true, but
  the current implementation already requires same length, so the
  docstring elsewhere ("As long as all expected lines are present")
  contradicts itself. Decide on a multiset semantics and document it.
- [x] `LegacyParser` in `src/apps/cli/main.py` accepts a positional
  `config_file` but the wrapper code in `main()` already special-cases
  `*.json` first. The legacy fallback is unreachable when the file does
  not end in `.json`; remove or document.
- [x] `student_submission` route never persists submissions or implements
  the intended non-exam exercise flow. For normal exercises, students
  should be able to submit their code to the server, have it executed
  immediately against the configured test cases, and receive structured
  results back right away for self-service feedback. The current route
  still contains the placeholder comment "In a real implementation, this
  would: 1. Store the submission in a database…".
- [x] `metrics_router` `get_system_stats` returns `rate_limiter:
  {"status": "active"}` regardless of actual state — placeholder code.
- [x] `update_test_suite` route uses `from_test_suite_config_server`
  which always overwrites all stored execution data with the new file —
  no per-tenant separation, no validation that paths exist, no error
  responses.
- [x] `parse_config_data` in `configuration_data.py` returns whatever
  is in `test.db`, but `update_execution_manager_data` writes to the
  same `test.db`; meanwhile `app.state.db = Database("testio.db")` —
  two separate databases used by different code paths.
- [x] `ExecutionManagerDataTable.__init__` opens a context but never
  closes it inside a `with` (relies on `close()`); double-close is silent
  but errors leak the connection.
- [x] `RateLimitMiddleware._get_client_id` does not validate
  `X-Forwarded-For` against trusted proxies — easy to spoof.
- [x] `RateLimitMiddleware` exempts `/docs` and `/openapi.json` but not
  `/redoc` data endpoints; either both or neither.
- [x] `Database.__exit__` commits even when `exc_type` indicates failure
  — should `rollback()` on exception.
- [x] `Database.cursor` is shared across threads through the singleton;
  SQLite cursors are not thread-safe even with `check_same_thread=False`.
- [x] `execute_check` / `student.py` — `subprocess.run(["python3", ...])`
  hard-codes `python3`; on Windows or CI without `python3`, this fails.
  Use `sys.executable`.
- [x] `student.py:detect_language` returns `"nodejs"` for `.js` but
  `check_syntax` does not handle `nodejs`; outputs unsupported warning.
- [x] CLI `run` command writes a JSON report timestamped with
  `report_{datetime.now()}.json` — racy if two runs start in same second.
- [x] `process_file_for_server` annotation `results: list[ComparisonOutputData]`
  uses PEP585 generics, requires Python 3.9+.
- [x] `validation.sanitize_output` truncates at 50_000 chars but the
  result is appended with `"\n... (output truncated)"`, so length now
  exceeds the limit; harmless but not what the docstring claims.
- [~] `interactive_runner.run_interleaved` doesn't actually do
  interleaving — it joins all inputs with `\n` and calls `communicate`
  exactly like `Runner` does. The whole module is mis-named; either
  implement true line-by-line interaction (read prompt → write input)
  or delete the runner and document it as a sequential variant.

---

## 3. Server / API expansions

- [x] Implement real persistence for `/student_submission` (DB table,
  pagination, retrieval API).
- [x] Add a dedicated normal-exercise submission workflow separate from
  exam mode: student uploads code -> server stores submission -> executes
  against the exercise test suite -> returns immediate per-test results,
  summary stats, and compiler/runtime errors in the same response.
- [~] Add WebSocket / SSE endpoint for live test progress instead of
  polling.
- [x] Add `DELETE /api/exam/session/{id}` and a soft-delete flag for
  GDPR-style cleanup.
- [x] Add bulk export endpoint covering all sessions.
- [~] Add per-test-case scoring weights & partial credit.
- [x] Add an OpenAPI security scheme once auth is added.
- [x] Add `/healthz` (Kubernetes-style liveness/readiness split).
- [~] Make rate-limit storage pluggable (Redis backend) so it works
  across multiple workers/replicas.
- [x] Configurable max upload size for `homework_submission`.
- [x] Validate `config_file` upload content-type & size in
  `/homework_submission`.
- [x] `student_submission` should accept attachments / multiple files.

---

## 4. CLI improvements

- [ ] Replace hand-rolled argparse with `click` or `typer` for cleaner
  subcommands, shell completion, colored help.
- [x] Add `testio --version` and embed version in `pyproject.toml`.
- [x] Add machine-readable `--format json|junitxml|tap` output for
  `testio run` so it integrates with CI dashboards.
- [x] JUnit XML output enables consumption by GitHub Actions, Jenkins,
  GitLab, etc.
- [ ] Add `testio watch <config>` for re-running tests on file change.
- [ ] Add `testio diff` to compare two runs.
- [ ] Move ANSI color handling behind `colorama` / `rich` (Windows
  terminals do not interpret raw ANSI escapes by default).
- [x] `result_renderer` has 4 nearly-identical `Strategy` classes; collapse
  via a small data-driven renderer.
- [x] `student check` should auto-resolve a config from the current
  directory (e.g., `./config.json`) instead of requiring it explicitly.

---

## 5. Tests & QA

- [~] No tests currently exist for: `connection_pool`, `execution.queue`,
  `caching.memory_cache`, `middleware`, `rate_limiter`, `validation`,
  `compiler`, `interactive_runner`, the new `student/init/generate/export`
  CLI commands, the `/api/metrics`, `/api/stats`, `/api/export` routes.
  Add unit + integration coverage.
- [x] Add a `pytest` configuration (`pyproject.toml [tool.pytest.ini_options]`
  or `pytest.ini`) so `pythonpath`, markers, and asyncio mode are
  declared. Currently tests rely on `sys.path` hacks.
- [x] Add `pytest-cov` and a coverage gate in CI (e.g., `--cov-fail-under=80`).
- [x] Add `pytest-asyncio` for async route tests; add `httpx.AsyncClient`
  fixtures for the FastAPI app instead of relying on side effects.
- [x] Add property-based tests (`hypothesis`) for the comparator (regex,
  unordered, plain).
- [x] Add tests that confirm the legacy `command` vs `run_command` vs
  `compile_command` precedence rules from the README.
- [x] Add tests for the CLI entry points using `argparse`'s exit codes.
- [x] Add an end-to-end test that boots the FastAPI app with TestClient
  and exercises every router.
- [x] Add test that the timeout path actually kills the child (assert
  no zombie processes).
- [ ] Add tests for symlink/relative-path edge cases in
  `from_test_suite_config_local`.

---

## 6. CI/CD

- [x] **`.github/workflows/python-app.yml`** is broken: the "Lint with
  black" step runs `black .` (which *formats* files) — it never fails the
  build. Replace with `black --check --diff .`.
- [x] Bump action versions: `actions/checkout@v2 → @v4`,
  `actions/setup-python@v2 → @v5`.
- [x] Run on a matrix of Python versions (3.10, 3.11, 3.12) and OSes
  (ubuntu, macos, windows).
- [x] Add `ruff` (or `flake8 + isort + autoflake`) and `mypy` (strict
  mode) to CI.
- [x] Cache pip downloads (`actions/setup-python` already supports
  `cache: pip`).
- [x] Upload coverage artifact + Codecov badge.
- [x] Run `bandit` + `pip-audit` for security scanning.
- [x] Add Dependabot/renovate for dependency updates.
- [x] Add `release.yml` workflow that publishes to PyPI on tag.
- [ ] `nuitka-build.yml` builds binaries for 4 apps × 3 OSes — verify
  `scripts/student_ui.py`, `scripts/teacher_ui.py`, etc., still exist
  and work; today they're untested.
- [x] Add a Docker image build workflow (multi-arch) so the server can
  be deployed easily.

---

## 7. Documentation

- [~] **README** rewrite:
  - [x] Fix `LICENSE.txt` link (file is `LICENSE`).
  - [x] Update Python requirement to actual minimum.
  - [ ] List *all* runtime requirements (jinja2, python-multipart,
        starlette, etc., currently hidden in `requirements.txt`).
  - [ ] Replace `virtualenv` instructions with `python -m venv`.
  - [ ] Document the new packaged entrypoints (`testio …`,
        `testio-server …`) once packaging is added.
  - [x] Document authentication once added.
  - [x] Document the security model + sandboxing assumptions.
  - [ ] Add a quickstart for Docker.
  - [x] Replace remaining "Flask templates" wording in *Future Development*
        — the project uses FastAPI/Jinja2, not Flask.
  - [ ] Add a screenshot/animated GIF for both teacher and student
        modes.
- [ ] **API docs** — augment FastAPI route docstrings with response
  schemas and example payloads. The auto-generated `/docs` page is
  currently sparse.
- [ ] **Sphinx docs** under `docs/`: only an empty `index.rst` plus a
  `modules.rst`; auto-generate API reference with `sphinx-apidoc`, build
  in CI, and publish via GitHub Pages or Read the Docs.
- [~] Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `CHANGELOG.md` (Keep a Changelog format).
- [x] Add an issue/PR template under `.github/`.
- [x] Document each `examples/` sub-directory with a short README so
  new users know what each example demonstrates.
- [x] Document the JSON config schema as a JSON-Schema file
  (`schemas/testio-config.schema.json`) and validate against it in
  `ConfigParser.validate` (currently a hand-rolled half-validator).

---

## 8. Frontend (server templates / static assets)

- [x] Static JS files compare against `'ComparisonResult.MATCH'` literal —
  must change in lock-step with the backend enum-string fix
  (`student_exam.js`, `student.js`, `exam.js`, plus the `old/` set if
  not deleted).
- [ ] Bundle/minify static assets, or migrate to a small frontend
  framework (Vue/Svelte) under `web/`; currently raw JS+CSS with
  no build step.
- [ ] Add ARIA labels and keyboard navigation; verify color contrast.
- [ ] Provide a dark mode (toggle in menubar).
- [ ] Internationalize strings; only English is hard-coded.
- [ ] Replace inline styles with class names where present.

---

## 9. Hooks & developer tooling

- [x] Replace ad-hoc `hooks/setup_hooks.sh` with [pre-commit](https://pre-commit.com/),
  configured via `.pre-commit-config.yaml` (black, isort, ruff, mypy,
  end-of-file-fixer, trailing-whitespace, JSON sort).
- [x] `hooks/run_all.sh` is referenced from `setup_hooks.sh` but should
  be reviewed for correctness once pre-commit replaces it.
- [x] Add a `Makefile` (or `justfile`) with targets: `make test`,
  `make lint`, `make fmt`, `make docs`, `make serve`, `make docker`.
- [x] Add an `.editorconfig`.

---

## 10. Examples & assets

- [ ] Add expected output snapshots / sample reports under
  `examples/*/expected/` so users can verify behavior without running.
- [ ] Add a multi-language example (one C, one Java, one Python) showing
  `compile_command` + `run_command` together.
- [ ] Add an example with `unordered: true` and one with `interleaved: true`.
- [ ] `resources/diagram.png` (referenced by README) — verify it still
  matches the actual architecture; regenerate if not.
- [x] Several example directories include compiled artifacts in
  `.gitignore` patterns — make sure they're not accidentally committed.

---

## 11. Observability & ops

- [ ] Replace homemade `MetricsCollector` with Prometheus
  (`prometheus-client`) and expose `/metrics` in OpenMetrics format.
- [x] Add structured logging (JSON via `structlog` or `python-json-logger`).
- [ ] Add OpenTelemetry tracing hooks for FastAPI + sqlite.
- [x] Add a Dockerfile + docker-compose with Postgres/Redis options and
  document deployment.
- [x] Add health checks suitable for kubelet (`/livez`, `/readyz`).

---

## 12. Database

- [ ] Migrate from raw SQLite + ad-hoc `CREATE TABLE IF NOT EXISTS` to
  Alembic migrations + SQLAlchemy (or SQLModel) models.
- [x] Add proper indexes on `student_submissions(session_id)`,
  `student_submissions(submitted_at)`, `exam_sessions(is_active)`.
- [x] Add a `closed_at` timestamp on `exam_sessions` and never serve
  ended sessions.
- [~] Add cascade-delete (foreign-key `ON DELETE CASCADE`) and turn on
  `PRAGMA foreign_keys = ON` (currently only enabled in the unused
  `ConnectionPool`).
- [ ] Add backup / vacuum scheduling guidance.

---

## 13. Cleanup

- [x] Delete `src/apps/server/old/` (legacy templates/static).
- [x] Delete unreferenced helper functions in `core/utils/misc.py` if
  unused (e.g., `files_in_dir`, `ensure_correct_newlines` only used in
  one place — verify and inline or keep).
- [x] Remove `# TODO: This method is unnecessary…` after consolidating
  the factory.
- [x] Drop `program.py` from `.gitignore` if no longer relevant.
- [x] Audit and delete any `*.bak`, `__pycache__`, `*.pyc` once a
  proper `.gitignore`/CI cache strategy is in place.

---

## Suggested execution order

1. Section 0 (security/correctness) — must precede any public deployment.
2. Section 1 (packaging + remove `sys.path` hacks) — unblocks tests/CI.
3. Section 6 (fix CI lint, bump actions) — gives a real safety net.
4. Section 5 (tests) — write before refactoring.
5. Sections 2 & 12 (functional bugs, DB migration).
6. Sections 3, 4, 8 (feature work).
7. Sections 7, 9, 10, 11, 13 (polish, ops, docs).
