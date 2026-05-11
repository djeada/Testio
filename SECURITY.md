# Security Policy

## Supported Versions

Only the latest release receives security updates.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, email the maintainer directly or open a [GitHub Security Advisory](https://github.com/djeida/Testio/security/advisories/new).

We aim to respond within 72 hours and release a fix within 14 days for confirmed vulnerabilities.

## Security Model

- Student code is executed in a subprocess with POSIX resource limits (CPU and memory) when `TESTIO_SANDBOX_CPU_SECS` and `TESTIO_SANDBOX_MEM_MB` are configured.
- For production deployments, use container isolation (Docker, nsjail, etc.) in addition to `setrlimit`.
- Teacher endpoints are protected by `TESTIO_TEACHER_API_KEY`. Set this in production.
- CORS origins must be explicitly configured via `TESTIO_ALLOW_ORIGINS`.
