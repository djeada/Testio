"""Regression tests for the server security / correctness hardening."""

import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from testio.apps.server.database.exam_sessions import (
    DuplicateSubmissionError,
    ExamSessionsTable,
)
from testio.apps.server.middleware import (
    BodySizeLimitMiddleware,
    ErrorHandlingMiddleware,
)
from testio.core.execution.queue import QueueFullError

PY_CONFIG = {
    "command": "python3",
    "path": "program.py",
    "tests": [
        {"input": ["2", "3"], "output": ["5"], "timeout": 5},
        {"input": ["10", "20"], "output": ["30"], "timeout": 5},
    ],
}
SUM_PROGRAM = "a = int(input())\nb = int(input())\nprint(a + b)\n"


def _files(config, programs):
    files = [
        (
            "config_file",
            (
                "config.json",
                io.BytesIO(json.dumps(config).encode()),
                "application/json",
            ),
        )
    ]
    for name, content in programs:
        files.append(
            ("student_files", (name, io.BytesIO(content.encode()), "text/plain"))
        )
    return files


# ---------------------------------------------------------------------------
# 1. Endpoints that take a config from the caller require teacher auth
# ---------------------------------------------------------------------------


def test_homework_submission_requires_teacher(anon_client):
    response = anon_client.post(
        "/homework_submission", files=_files(PY_CONFIG, [("a.py", SUM_PROGRAM)])
    )
    assert response.status_code == 401


def test_exercise_submission_requires_teacher(anon_client, teacher_client):
    def post(client):
        return client.post(
            "/api/exercise/submit",
            data={"student_name": "alice"},
            files=[
                (
                    "code_file",
                    ("sum.py", io.BytesIO(SUM_PROGRAM.encode()), "text/plain"),
                ),
                (
                    "config_file",
                    (
                        "config.json",
                        io.BytesIO(json.dumps(PY_CONFIG).encode()),
                        "application/json",
                    ),
                ),
            ],
        )

    assert post(anon_client).status_code == 401
    response = post(teacher_client)
    assert response.status_code == 200
    assert response.json()["passed_tests"] == 2


def test_homework_rejects_disallowed_command(teacher_client):
    config = dict(PY_CONFIG, command="/bin/sh -c")
    response = teacher_client.post(
        "/homework_submission", files=_files(config, [("a.py", SUM_PROGRAM)])
    )
    assert response.status_code == 400


def test_homework_limits_file_count(teacher_client, monkeypatch):
    monkeypatch.setenv("TESTIO_MAX_UPLOAD_FILES", "2")
    programs = [(f"s{i}.py", SUM_PROGRAM) for i in range(3)]
    response = teacher_client.post(
        "/homework_submission", files=_files(PY_CONFIG, programs)
    )
    assert response.status_code == 413


def test_homework_limits_file_size(teacher_client, monkeypatch):
    monkeypatch.setenv("TESTIO_MAX_UPLOAD_SIZE_MB", "0.001")  # ~1 KB
    programs = [("big.py", "#" * 5000)]
    response = teacher_client.post(
        "/homework_submission", files=_files(PY_CONFIG, programs)
    )
    assert response.status_code == 413


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc not installed")
def test_homework_compiles_c_submissions(teacher_client):
    config = {
        "compile_command": "gcc {source} -o {output}",
        "path": "main.c",
        "tests": PY_CONFIG["tests"],
    }
    good = '#include <stdio.h>\nint main(){int a,b;scanf("%d %d",&a,&b);printf("%d\\n",a+b);return 0;}\n'
    bad = "int main( {"
    response = teacher_client.post(
        "/homework_submission", files=_files(config, [("good.c", good), ("bad.c", bad)])
    )
    assert response.status_code == 200
    good_result, bad_result = response.json()["student_results"]
    assert good_result["passed_tests"] == 2
    assert bad_result["passed_tests"] == 0
    assert bad_result["test_results"][0]["result_name"] == "EXECUTION_ERROR"
    assert "Compilation failed" in bad_result["test_results"][0]["error"]


# ---------------------------------------------------------------------------
# 2. Programs run in a private temporary directory with a scrubbed env
# ---------------------------------------------------------------------------


def test_execute_tests_runs_in_private_temp_dir(teacher_client, anon_client):
    config = {
        "command": "python3",
        "path": "probe.py",
        "tests": [{"input": [], "output": ["x"], "timeout": 5}],
    }
    assert teacher_client.post("/update_test_suite", json=config).status_code == 200

    probe = (
        "import os\n"
        "print(os.getcwd())\n"
        "print(sorted(os.listdir('.')))\n"
        "print(os.environ.get('TESTIO_TEACHER_API_KEY'))\n"
        "print(os.path.exists('app.db') or os.path.exists('testio.db'))\n"
    )
    response = anon_client.post("/execute_tests", json={"script_text": probe})
    assert response.status_code == 200
    cwd, listing, key, db_visible = response.json()["results"][0]["tests"][0][
        "output"
    ].splitlines()

    assert cwd != os.getcwd()
    assert Path(cwd).name.startswith("testio-run-")
    assert listing == "['build', 'probe.py']" or listing == "['probe.py']"
    assert key == "None"
    assert db_visible == "False"
    # Cleaned up afterwards.
    assert not Path(cwd).exists()


def test_execute_tests_without_suite_is_404(anon_client):
    response = anon_client.post("/execute_tests", json={"script_text": "print(1)"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 3/4. Exam answers stay private; joins, tokens and single submission
# ---------------------------------------------------------------------------


@pytest.fixture
def exam_session(teacher_client):
    response = teacher_client.post(
        "/api/exam/create_session", json={"config_data": PY_CONFIG}
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    assert len(session_id) >= 20  # unguessable
    return session_id


def test_exam_session_details_are_teacher_only(
    anon_client, teacher_client, exam_session
):
    assert anon_client.get(f"/api/exam/session/{exam_session}").status_code == 401
    full = teacher_client.get(f"/api/exam/session/{exam_session}")
    assert full.json()["config_data"]["tests"][0]["output"] == ["5"]

    public = anon_client.get(f"/api/exam/session/{exam_session}/public").json()
    assert public["total_tests"] == 2
    assert set(public) == {
        "session_id",
        "is_active",
        "created_at",
        "closed_at",
        "total_tests",
    }

    page = anon_client.get(f"/student/{exam_session}")
    assert page.status_code == 200
    assert '"output"' not in page.text


def test_exam_test_code_does_not_leak_answers(anon_client, exam_session):
    response = anon_client.post(
        "/api/exam/test_code",
        json={"session_id": exam_session, "student_id": "alice", "code": SUM_PROGRAM},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["passed_tests"] == 2
    for test in data["test_results"]:
        assert set(test) == {"test", "result_name", "result"}


def test_exam_join_and_single_submission(anon_client, teacher_client, exam_session):
    base = {"session_id": exam_session, "student_id": "alice", "code": SUM_PROGRAM}

    # No token: rejected (field is required).
    assert anon_client.post("/api/exam/submit_code", json=base).status_code == 422
    # Wrong token: rejected.
    bad = anon_client.post("/api/exam/submit_code", json={**base, "student_token": "x"})
    assert bad.status_code == 403

    joined = anon_client.post(
        "/api/exam/join", json={"session_id": exam_session, "student_id": "alice"}
    )
    assert joined.status_code == 200
    token = joined.json()["student_token"]

    # Someone else cannot claim the same ID.
    again = anon_client.post(
        "/api/exam/join", json={"session_id": exam_session, "student_id": "alice"}
    )
    assert again.status_code == 409

    ok = anon_client.post(
        "/api/exam/submit_code", json={**base, "student_token": token}
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["score"] == 100.0
    assert all(
        set(t) == {"test", "result_name", "result"} for t in body["test_results"]
    )

    dup = anon_client.post(
        "/api/exam/submit_code", json={**base, "student_token": token}
    )
    assert dup.status_code == 409

    subs = teacher_client.get(f"/api/exam/submissions/{exam_session}").json()
    assert subs["total_submissions"] == 1
    assert subs["submissions"][0]["test_results"][0]["expected_output"] == "5"

    # The teacher can release a claimed ID.
    released = teacher_client.delete(
        f"/api/exam/session/{exam_session}/participants/alice"
    )
    assert released.status_code == 200


def test_exam_rejects_invalid_student_id(anon_client, exam_session):
    response = anon_client.post(
        "/api/exam/join",
        json={"session_id": exam_session, "student_id": "<img src=x onerror=alert(1)>"},
    )
    assert response.status_code == 422


def test_ended_session_rejects_students(anon_client, teacher_client, exam_session):
    assert (
        teacher_client.post(f"/api/exam/end_session/{exam_session}").status_code == 200
    )
    response = anon_client.post(
        "/api/exam/test_code",
        json={"session_id": exam_session, "student_id": "bob", "code": SUM_PROGRAM},
    )
    assert response.status_code == 403


def test_end_unknown_session_is_404(teacher_client):
    assert (
        teacher_client.post("/api/exam/end_session/does-not-exist").status_code == 404
    )


def test_submit_student_work_is_atomic(tmp_path):
    table = ExamSessionsTable(str(tmp_path / "exam.db"))
    assert table.create_session("s1", {"tests": []})
    assert table.submit_student_work("s1", "alice", "print(1)", [], 100.0) is True
    with pytest.raises(DuplicateSubmissionError):
        table.submit_student_work("s1", "alice", "print(2)", [], 0.0)
    assert table.get_student_submission("s1", "alice")["student_code"] == "print(1)"


def test_session_lookup_is_not_stale_after_end(tmp_path):
    table = ExamSessionsTable(str(tmp_path / "exam.db"))
    table.create_session("s2", {"tests": []})
    assert table.get_session("s2")["is_active"] is True
    assert table.end_session("s2") is True
    assert table.get_session("s2")["is_active"] is False
    assert table.end_session("missing") is False


def test_participant_tokens(tmp_path):
    table = ExamSessionsTable(str(tmp_path / "exam.db"))
    table.create_session("s3", {"tests": []})
    token = table.register_participant("s3", "alice")
    assert token
    assert table.register_participant("s3", "alice") is None
    assert table.verify_participant("s3", "alice", token)
    assert not table.verify_participant("s3", "alice", "wrong")
    assert not table.verify_participant("s3", "bob", token)


# ---------------------------------------------------------------------------
# 5. Student submission review is teacher-only and bounded
# ---------------------------------------------------------------------------


def test_student_submissions_read_requires_teacher(anon_client, teacher_client):
    created = anon_client.post(
        "/student_submission",
        json={"student_name": "a", "problem_description": "p", "code": "print(1)"},
    )
    assert created.status_code == 200
    submission_id = created.json()["submission_id"]

    assert anon_client.get("/student_submissions").status_code == 401
    assert anon_client.get(f"/student_submissions/{submission_id}").status_code == 401
    assert (
        teacher_client.get(f"/student_submissions/{submission_id}").status_code == 200
    )


def test_student_submission_rejects_oversized_fields(anon_client):
    response = anon_client.post(
        "/student_submission",
        json={
            "student_name": "a" * 500,
            "problem_description": "p",
            "code": "print(1)",
        },
    )
    assert response.status_code == 422


def test_request_body_limit(anon_client, monkeypatch):
    monkeypatch.setenv("TESTIO_MAX_REQUEST_SIZE_MB", "0.01")  # ~10 KB
    response = anon_client.post(
        "/student_submission",
        json={"student_name": "a", "problem_description": "p", "code": "x" * 20000},
    )
    assert response.status_code == 413


def test_body_limit_applies_to_streamed_bodies():
    app = FastAPI()

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return {"size": len(json.dumps(payload))}

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=100)

    def chunks():
        yield b'{"a": "'
        yield b"x" * 500
        yield b'"}'

    with TestClient(app) as client:
        response = client.post(
            "/echo", content=chunks(), headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# 7. Queue saturation becomes 503 + Retry-After
# ---------------------------------------------------------------------------


def test_queue_full_returns_503(anon_client, teacher_client, monkeypatch):
    assert teacher_client.post("/update_test_suite", json=PY_CONFIG).status_code == 200

    class FullQueue:
        max_workers = 1

        async def submit_async(self, *args, **kwargs):
            raise QueueFullError()

    import testio.apps.server.execution as execution_module

    monkeypatch.setattr(execution_module, "get_execution_queue", lambda: FullQueue())
    response = anon_client.post("/execute_tests", json={"script_text": SUM_PROGRAM})
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"


# ---------------------------------------------------------------------------
# 9. Config cache invalidation
# ---------------------------------------------------------------------------


def test_update_test_suite_is_visible_immediately(teacher_client, anon_client):
    first = dict(PY_CONFIG, tests=[{"input": [], "output": ["one"], "timeout": 5}])
    second = dict(PY_CONFIG, tests=[{"input": [], "output": ["two"], "timeout": 5}])
    teacher_client.post("/update_test_suite", json=first)
    run1 = anon_client.post("/execute_tests", json={"script_text": "print('two')"})
    teacher_client.post("/update_test_suite", json=second)
    run2 = anon_client.post("/execute_tests", json={"script_text": "print('two')"})
    assert run1.json()["total_passed_tests"] == 0
    assert run2.json()["total_passed_tests"] == 1


def test_legacy_parse_config_cache_invalidated():
    from testio.apps.server.database.configuration_data import (
        parse_config_data,
        update_execution_manager_data,
    )
    from testio.core.execution.data import ExecutionManagerInputData

    update_execution_manager_data({"a.py": [ExecutionManagerInputData(command="x")]})
    assert list(parse_config_data()) == ["a.py"]
    update_execution_manager_data({"b.py": [ExecutionManagerInputData(command="y")]})
    assert list(parse_config_data()) == ["b.py"]


# ---------------------------------------------------------------------------
# 14. Errors, metrics and statistics
# ---------------------------------------------------------------------------


def test_error_middleware_hides_exception_text():
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/boom")
    def boom():
        raise ValueError("/secret/path/testio.db is locked")

    with TestClient(app) as client:
        response = client.get("/boom")
    assert response.status_code == 400
    assert "secret" not in response.text


def test_operational_endpoints_require_teacher(
    anon_client, teacher_client, exam_session
):
    for path in (
        "/api/metrics",
        "/api/metrics/system",
        "/api/metrics/cache",
        f"/api/stats/session/{exam_session}",
        f"/api/stats/leaderboard/{exam_session}",
    ):
        assert anon_client.get(path).status_code == 401, path
        assert teacher_client.get(path).status_code == 200, path

    system = teacher_client.get("/api/metrics/system").json()
    assert "database_path" not in system["database"]


# ---------------------------------------------------------------------------
# 15. Importing the server module has no side effects
# ---------------------------------------------------------------------------


def test_importing_server_module_creates_no_database(tmp_path):
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("TESTIO_")
    }
    subprocess.run(
        [sys.executable, "-c", "import testio.apps.server.app.testio_server"],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
    )
    assert not (tmp_path / "testio.db").exists()


# ---------------------------------------------------------------------------
# 13. Static JS escapes untrusted data
# ---------------------------------------------------------------------------


def test_static_js_escapes_untrusted_values():
    js_dir = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "testio"
        / "apps"
        / "server"
        / "static"
        / "js"
    )
    homework = (js_dir / "homework.js").read_text()
    assert "${student.student_name}" not in homework
    assert "escapeHtml(student.student_name)" in homework
    assert "${file.name}" not in homework.replace("`${index + 1}. ${file.name}`", "")
    for name in ("exam.js", "student_exam.js"):
        source = (js_dir / name).read_text()
        assert "${message}" not in source, name
