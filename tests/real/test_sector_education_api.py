#!/usr/bin/env python3
"""
ASIMNEXUS Education Sector API Tests
=====================================
Tests for all education sector endpoints: student enrollment, course management,
grade updates, graduation, and statistics.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_education_sector():
    """Mock EducationSector with realistic return values."""
    mock = MagicMock()

    mock.enroll_student.return_value = {
        "status": "enrolled",
        "student_id": "stu_001",
        "name": "Alice Student",
        "program": "Computer Science",
        "enrolled_at": "2025-01-15T00:00:00",
    }

    mock.create_course.return_value = {
        "status": "created",
        "course_id": "cs_101",
        "name": "Intro to Programming",
        "code": "CS101",
        "credits": 3,
    }

    mock.enroll_in_course.return_value = {
        "status": "enrolled",
        "student_id": "stu_001",
        "course_id": "cs_101",
        "enrolled_at": "2025-01-20T00:00:00",
    }

    mock.update_grades.return_value = {
        "status": "updated",
        "student_id": "stu_001",
        "gpa": 3.7,
        "credits_earned": 30,
    }

    mock.graduate_student.return_value = {
        "status": "graduated",
        "student_id": "stu_001",
        "name": "Alice Student",
        "degree": "BSc Computer Science",
        "graduated_at": "2026-06-01T00:00:00",
    }

    mock_student = MagicMock()
    mock_student.to_dict.return_value = {
        "student_id": "stu_001",
        "name": "Alice Student",
        "program": "Computer Science",
        "status": "active",
        "gpa": 3.7,
    }
    mock.get_student.return_value = mock_student

    mock_course = MagicMock()
    mock_course.to_dict.return_value = {
        "course_id": "cs_101",
        "name": "Intro to Programming",
        "code": "CS101",
        "credits": 3,
        "department": "CS",
    }
    mock.get_course.return_value = mock_course

    mock.list_students.return_value = [mock_student]
    mock.list_courses.return_value = [mock_course]

    mock.get_stats.return_value = {
        "total_students": 1,
        "total_courses": 1,
        "active_enrollments": 1,
        "graduation_rate": 0.9,
        "average_gpa": 3.7,
    }

    return mock


@pytest.fixture
def client(mock_education_sector):
    """Create test client with mocked education sector."""
    app = FastAPI()
    with patch("core.api_endpoints.sector_api._get_education",
               return_value=mock_education_sector):
        from core.api_endpoints.sector_api import router
        app.include_router(router)
        yield TestClient(app)


# ─── Student Management Tests ────────────────────────────────────────────────


class TestEducationStudentManagement:
    """Tests for student enrollment and management."""

    def test_enroll_student_success(self, client, mock_education_sector):
        """POST /api/sectors/education/enroll enrolls a student."""
        response = client.post("/api/sectors/education/enroll", json={
            "student_id": "stu_001",
            "name": "Alice Student",
            "email": "alice@university.edu",
            "phone": "555-0300",
            "date_of_birth": "2000-01-01",
            "address": "123 College Ave",
            "program": "Computer Science",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "enrolled"
        assert data["student_id"] == "stu_001"
        mock_education_sector.enroll_student.assert_called_once()

    def test_enroll_student_unavailable(self, client):
        """Returns 503 when EducationSector is not available."""
        with patch("core.api_endpoints.sector_api._get_education", return_value=None):
            response = client.post("/api/sectors/education/enroll", json={
                "student_id": "stu_002",
                "name": "Bob Student",
            })
            assert response.status_code == 503

    def test_list_students(self, client, mock_education_sector):
        """GET /api/sectors/education/students lists all students."""
        response = client.get("/api/sectors/education/students")
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        mock_education_sector.list_students.assert_called_once_with(None)

    def test_list_students_by_program(self, client, mock_education_sector):
        """GET /api/sectors/education/students?program=CS filters by program."""
        response = client.get("/api/sectors/education/students", params={"program": "CS"})
        assert response.status_code == 200
        mock_education_sector.list_students.assert_called_with("CS")

    def test_get_student_by_id(self, client, mock_education_sector):
        """GET /api/sectors/education/student/{id} returns student details."""
        response = client.get("/api/sectors/education/student/stu_001")
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "stu_001"
        mock_education_sector.get_student.assert_called_once_with("stu_001")

    def test_get_student_not_found(self, client, mock_education_sector):
        """Returns 404 for non-existent student."""
        mock_education_sector.get_student.return_value = None
        response = client.get("/api/sectors/education/student/nonexistent")
        assert response.status_code == 404


# ─── Course Management Tests ─────────────────────────────────────────────────


class TestEducationCourseManagement:
    """Tests for course creation and management."""

    def test_create_course_success(self, client, mock_education_sector):
        """POST /api/sectors/education/courses creates a course."""
        response = client.post("/api/sectors/education/courses", json={
            "course_id": "cs_101",
            "name": "Intro to Programming",
            "code": "CS101",
            "description": "Learn programming fundamentals",
            "level": "undergraduate",
            "credits": 3,
            "department": "CS",
            "instructor": "Dr. Smith",
            "capacity": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["course_id"] == "cs_101"
        mock_education_sector.create_course.assert_called_once()

    def test_list_courses(self, client, mock_education_sector):
        """GET /api/sectors/education/courses lists all courses."""
        response = client.get("/api/sectors/education/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        mock_education_sector.list_courses.assert_called_once_with(None)

    def test_get_course_by_id(self, client, mock_education_sector):
        """GET /api/sectors/education/course/{id} returns course details."""
        response = client.get("/api/sectors/education/course/cs_101")
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == "cs_101"
        mock_education_sector.get_course.assert_called_once_with("cs_101")

    def test_get_course_not_found(self, client, mock_education_sector):
        """Returns 404 for non-existent course."""
        mock_education_sector.get_course.return_value = None
        response = client.get("/api/sectors/education/course/nonexistent")
        assert response.status_code == 404


# ─── Enrollment & Grade Tests ────────────────────────────────────────────────


class TestEducationEnrollmentGrades:
    """Tests for course enrollment, grades, and graduation."""

    def test_enroll_in_course_success(self, client, mock_education_sector):
        """POST /api/sectors/education/enroll-course enrolls student in course."""
        response = client.post("/api/sectors/education/enroll-course", json={
            "student_id": "stu_001",
            "course_id": "cs_101",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "enrolled"
        mock_education_sector.enroll_in_course.assert_called_once()

    def test_update_grades_success(self, client, mock_education_sector):
        """POST /api/sectors/education/grades updates student grades."""
        response = client.post("/api/sectors/education/grades", json={
            "student_id": "stu_001",
            "gpa": 3.7,
            "credits_earned": 30,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        mock_education_sector.update_grades.assert_called_once()

    def test_graduate_student_success(self, client, mock_education_sector):
        """POST /api/sectors/education/graduate/{student_id} graduates a student."""
        response = client.post("/api/sectors/education/graduate/stu_001")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "graduated"
        assert data["student_id"] == "stu_001"
        mock_education_sector.graduate_student.assert_called_once_with("stu_001")


# ─── Education Statistics Tests ──────────────────────────────────────────────


class TestEducationStats:
    """Tests for education statistics endpoint."""

    def test_education_stats(self, client, mock_education_sector):
        """GET /api/sectors/education/stats returns statistics."""
        response = client.get("/api/sectors/education/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data
        assert "total_courses" in data
        assert "graduation_rate" in data
        mock_education_sector.get_stats.assert_called_once()

    def test_education_stats_unavailable(self, client):
        """Returns 503 when EducationSector is not available."""
        with patch("core.api_endpoints.sector_api._get_education", return_value=None):
            response = client.get("/api/sectors/education/stats")
            assert response.status_code == 503
