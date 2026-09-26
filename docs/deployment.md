# Deploying the web UI

## Quick start with Docker (recommended)

```bash
export TESTIO_TEACHER_API_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up -d --build     # http://localhost:8000
```

The image runs as an unprivileged user and includes gcc/g++, Node.js and
Ruby (`docker compose build --build-arg INSTALL_JAVA=true` adds a JDK). The
compose file runs the container with a read-only filesystem and no Linux
capabilities, and caps its memory (2 GB), CPUs (2) and process count (256).
**These container limits are the real isolation boundary for student code.**
Size them for your class.

Data (SQLite databases) lives in the `testio_data` volume mounted at `/data`.

## Running directly

```bash
pip install .
export TESTIO_TEACHER_API_KEY=...
testio-server --mode teacher --host 127.0.0.1 --port 5000
testio-server --mode student --host 0.0.0.0 --port 5001
```

Only do this on a machine you are happy for student code to run on, as the
same OS user that runs the server.

## Authentication

Teacher-only features (homework grading, exam management, config upload,
submission lists, statistics, metrics) require the teacher key:

* **Browser**: open any teacher page and you are redirected to `/login`.
  Entering the key sets a signed, `HttpOnly`, `SameSite=Strict` session cookie
  valid for `TESTIO_SESSION_TTL_HOURS`. Set `TESTIO_SECURE_COOKIES=true` when
  serving over HTTPS.
* **API / scripts**: send the key as the `X-API-Key` header.

If no key is set, teacher endpoints **refuse requests**. The exceptions are a
server bound to loopback (`--host 127.0.0.1`), where direct local requests are
allowed, and `TESTIO_INSECURE_NO_AUTH=1`, which disables auth entirely (local
development only; a warning is logged).

### Exams

Students open `/student/<session id>`. On first use they claim a student ID
and receive a token (stored in the browser) that is required for their final
submission, so nobody else can submit under that ID. Exam responses contain
only pass/fail per test, never expected outputs, inputs or program output.
If a student loses their browser session, a teacher can release the ID with
`DELETE /api/exam/session/{id}/participants/{student_id}`.

## Reverse proxy

Put Testio behind a TLS-terminating proxy (nginx, Caddy, Traefik) for any
deployment reachable beyond localhost. Set `TESTIO_TRUSTED_PROXIES` to the
proxy's address so rate limiting sees real client IPs, and
`TESTIO_SECURE_COOKIES=true`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TESTIO_TEACHER_API_KEY` | unset | Teacher key (see above). Required for non-loopback deployments. |
| `TESTIO_INSECURE_NO_AUTH` | unset | `1` disables teacher auth. Development only. |
| `TESTIO_SESSION_TTL_HOURS` | `12` | Lifetime of the teacher login cookie. |
| `TESTIO_SECURE_COOKIES` | unset | `true` marks the login cookie `Secure` (HTTPS only). |
| `TESTIO_ALLOW_ORIGINS` | none | Comma-separated CORS origins. |
| `TESTIO_TRUSTED_PROXIES` | none | Comma-separated proxy IPs/CIDRs whose `X-Forwarded-For` is trusted. |
| `TESTIO_RATE_LIMIT_PER_MINUTE` | `120` | Requests per client per minute (`0` disables). Static files and health checks are exempt. |
| `TESTIO_MAX_REQUEST_SIZE_MB` | `50` | Maximum request body. |
| `TESTIO_MAX_UPLOAD_SIZE_MB` | `10` | Maximum size of one uploaded file. |
| `TESTIO_MAX_UPLOAD_FILES` | `200` | Maximum files per upload. |
| `TESTIO_MAX_CONCURRENT_EXECUTIONS` | `4` | Test runs executing at once. |
| `TESTIO_EXECUTION_QUEUE_SIZE` | `100` | Queued runs before the server answers `503` + `Retry-After`. |
| `TESTIO_MAX_TEST_TIMEOUT` | `300` | Largest `timeout` a config may request (seconds). |
| `TESTIO_MAX_OUTPUT_KB` | `1024` | Captured stdout/stderr per stream; larger output fails the test and kills the program. |
| `TESTIO_SANDBOX_CPU_SECS` | `30` | CPU-time rlimit for programs under test (`0` disables). |
| `TESTIO_SANDBOX_MEM_MB` | `512` | Address-space rlimit (`0` disables). Not applied to Node/Java, which reserve large address ranges; bound those with container memory limits. |
| `TESTIO_ALLOWED_EXECUTABLES` | none | Extra executables configs may use, e.g. `bash,php`. |
| `TESTIO_PASSTHROUGH_ENV` | none | Extra environment variables passed to programs under test (the environment is otherwise reduced to `PATH`, locale and toolchain variables). |
| `TESTIO_APP_DB_PATH` | `testio.db` | Exams/submissions database. |
| `TESTIO_CONFIG_DB_PATH` | `test.db` | Loaded test-suite database. |
| `TESTIO_LOG_LEVEL` | `INFO` | Log level. |
| `TESTIO_LOG_FORMAT` | `text` | `json` for structured logs. |

## Health and monitoring

* `GET /livez`: process is up (used by the Docker health check).
* `GET /readyz`: dependencies (database) are usable.
* `GET /api/metrics…`: execution metrics (teacher auth).

## Backups

Both databases are SQLite files in `/data`. Back them up with
`sqlite3 /data/testio.db ".backup '/backup/testio.db'"` (safe while the
server runs) rather than copying the file.
