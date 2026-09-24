# Testio backlog

The September 2026 audit fixed the correctness, security, packaging and
deployment defects found in the engine, CLI and server (see the
`audit/production-hardening` branch). What remains, highest value first:

## Isolation
- [ ] Optional per-execution isolation backend (nsjail / bubblewrap / one
  container per run) behind a setting, so a single server can grade untrusted
  code without relying only on the outer container. See SECURITY.md.
- [ ] Cgroup-based memory limit, so Node/Java get a memory cap too (rlimits
  cannot bound them).
- [ ] Kill a running execution when its queue task is cancelled (today the
  process's own timeout is relied on).

## Identity and auth
- [ ] Real student identity for exams (class roster with per-student codes,
  or SSO). Student IDs are first-come today.
- [ ] Lock out or slow down repeated failed teacher logins.
- [ ] Reject unauthenticated uploads before the body is received (auth check
  in middleware for multipart routes).

## Engine
- [ ] True interactive (prompt-by-prompt) execution for `interleaved` tests;
  input is currently supplied up front.
- [ ] Optional whitespace-insensitive and float-tolerance comparison modes.
- [ ] Per-test weights / partial credit.
- [ ] Clean up compile output directories after CLI runs (they are removed at
  process exit today; server runs clean up per request).

## Server
- [ ] Share the loaded test suite across multiple uvicorn workers without the
  30 s cache delay.
- [ ] Re-save suites loaded by versions before 0.2.0 so compiled-language
  suites go through the new build path.
- [ ] Live progress for long batch runs (SSE/WebSocket).
- [ ] Accessibility pass on the web UI (ARIA labels, keyboard navigation,
  contrast) and a dark mode.

## Project
- [ ] Hash-pinned lock file (`pip-compile --generate-hashes` / `uv lock`) for
  Docker and CI.
- [ ] Configure PyPI trusted publishing (the `pypi` environment used by
  `.github/workflows/release.yml`) before the first tagged release.
- [ ] Screenshots of the teacher and student UIs in the README.
- [ ] `testio watch` (re-run on file change) and `testio diff` (compare two
  JSON reports).
