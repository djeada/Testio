# Security Policy

## Supported versions

Only the latest release receives security updates.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.
Open a [GitHub Security Advisory](https://github.com/djeada/Testio/security/advisories/new)
instead. We aim to respond within 72 hours and to release a fix for confirmed
issues within 14 days.

## Threat model

Testio's job is to **run code it did not write**. Treat every program under
test, and on the server every submission, as hostile.

### What Testio does to limit damage

For every program it runs, Testio:

* runs it without a shell, as an argument list, from an executable allow-list;
* passes a reduced environment (`PATH`, locale and toolchain variables only),
  so API keys and credentials in the server's environment are not visible;
* applies POSIX rlimits for CPU time, address space (except Node/Java), file
  size and core dumps;
* enforces a wall-clock timeout and kills the **whole process group**, so
  background children cannot outlive the test;
* caps captured output, so an output flood cannot exhaust server memory;
* on the server, runs each request in a fresh private temporary directory
  that is deleted afterwards.

The web server additionally:

* requires the teacher key for every teacher capability and **fails closed**
  when no key is configured (except on loopback), comparing keys in constant
  time;
* never sends expected outputs, hidden inputs or program output to exam
  students, and binds exam submissions to a per-student token;
* escapes all user-controlled data in the UI and in exported reports;
* limits request and upload sizes, rate-limits clients and bounds the
  execution queue.

### What it does not do

These measures are **not a sandbox**. A submitted program still runs as the
server's OS user. It can read any file that user can read by absolute path,
open network connections, and use as much memory as Node/Java allow. Anyone
accepting submissions from people they do not fully trust must add a real
isolation boundary:

* **Recommended:** the provided Docker/compose setup (non-root, read-only
  filesystem, no capabilities, memory/CPU/PID limits), with no secrets
  mounted into the container other than the teacher key.
* For stronger isolation, run the grader on a dedicated VM or put each
  execution in nsjail, bubblewrap or gVisor.

### Known limitations

* Exam student IDs are first-come: someone who knows a classmate's ID can
  claim it before them. The teacher can release a claimed ID. There is no
  per-student login.
* Login attempts are only covered by the general rate limit; there is no
  lockout after repeated failures. Use a long random key.
* A multipart upload is received (up to `TESTIO_MAX_REQUEST_SIZE_MB`) before
  an unauthenticated request is rejected.
