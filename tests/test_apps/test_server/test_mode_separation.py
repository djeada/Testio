"""Tests for the application mode separation (student vs teacher)."""
import sys

sys.path.append(".")

import pytest
from fastapi.testclient import TestClient

from src.apps.server.app.testio_server import create_app


class TestApplicationModes:
    """Test class for application mode functionality."""

    @pytest.fixture
    def teacher_client(self):
        """Create a test client for teacher mode."""
        app = create_app(mode="teacher")
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def student_client(self):
        """Create a test client for student mode."""
        app = create_app(mode="student")
        with TestClient(app) as client:
            yield client

    def test_teacher_mode_index_page(self, teacher_client):
        """Test that teacher mode renders the teacher home page."""
        response = teacher_client.get("/")
        assert response.status_code == 200
        # Teacher mode should have teacher-specific content
        assert "Teacher" in response.text
        assert "Config Generator" in response.text or "Homework Mode" in response.text or "Examination Mode" in response.text

    def test_student_mode_index_page(self, student_client):
        """Test that student mode renders the student home page."""
        response = student_client.get("/")
        assert response.status_code == 200
        # Student mode should have student-specific content
        assert "Student" in response.text
        assert "My Workspace" in response.text or "Start Coding" in response.text

    def test_teacher_mode_has_config_generator(self, teacher_client):
        """Test that teacher mode has access to config generator."""
        response = teacher_client.get("/config-generator")
        assert response.status_code == 200

    def test_student_mode_no_config_generator(self, student_client):
        """Test that student mode does not have access to config generator."""
        response = student_client.get("/config-generator")
        # Should return 404 as the route is not registered
        assert response.status_code == 404

    def test_teacher_mode_has_homework(self, teacher_client):
        """Test that teacher mode has access to homework mode."""
        response = teacher_client.get("/homework")
        assert response.status_code == 200

    def test_student_mode_no_homework(self, student_client):
        """Test that student mode does not have access to homework mode."""
        response = student_client.get("/homework")
        # Should return 404 as the route is not registered
        assert response.status_code == 404

    def test_teacher_mode_has_exam(self, teacher_client):
        """Test that teacher mode has access to exam mode."""
        response = teacher_client.get("/exam")
        assert response.status_code == 200

    def test_student_mode_no_exam(self, student_client):
        """Test that student mode does not have access to exam mode."""
        response = student_client.get("/exam")
        # Should return 404 as the route is not registered
        assert response.status_code == 404

    def test_student_mode_has_student_page(self, student_client):
        """Test that student mode has access to student workspace."""
        response = student_client.get("/student")
        assert response.status_code == 200

    def test_teacher_mode_has_student_page(self, teacher_client):
        """Test that teacher mode can preview student page."""
        response = teacher_client.get("/student")
        assert response.status_code == 200

    def test_student_mode_has_execute_tests(self, student_client):
        """Test that student mode has access to execute tests API."""
        response = student_client.post("/execute_tests", json={"script_text": "print('hello')"})
        # Should return 200 (may fail without config, but route exists)
        assert response.status_code in [200, 400, 500]

    def test_teacher_mode_menubar(self, teacher_client):
        """Test that teacher mode uses teacher menubar."""
        response = teacher_client.get("/")
        assert response.status_code == 200
        # Teacher menubar should show teacher badge
        assert 'mode-badge teacher' in response.text or 'Teacher' in response.text

    def test_student_mode_menubar(self, student_client):
        """Test that student mode uses student menubar."""
        response = student_client.get("/")
        assert response.status_code == 200
        # Student menubar should show student badge
        assert 'mode-badge student' in response.text or 'Student' in response.text

    def test_default_mode_is_teacher(self):
        """Test that default mode is teacher when not specified."""
        app = create_app()  # No mode specified
        assert app.state.mode == "teacher"

    def test_app_state_stores_mode(self):
        """Test that the mode is stored in app state."""
        teacher_app = create_app(mode="teacher")
        student_app = create_app(mode="student")
        
        assert teacher_app.state.mode == "teacher"
        assert student_app.state.mode == "student"
