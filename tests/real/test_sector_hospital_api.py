#!/usr/bin/env python3
"""
ASIMNEXUS Hospital Sector API Tests
====================================
Tests for all hospital sector endpoints: registration, admission, discharge,
patient listing, and statistics.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_hospital_sector():
    """Mock HospitalSector with realistic return values."""
    mock = MagicMock()

    # register_hospital
    mock.register_hospital.return_value = {
        "status": "registered",
        "hospital_id": "hosp_001",
        "name": "Test Hospital",
        "department_count": 10,
        "bed_count": 100,
        "staff_count": 50,
        "registered_at": "2025-01-01T00:00:00",
    }

    # admit_patient
    mock.admit_patient.return_value = {
        "status": "admitted",
        "patient_id": "pat_001",
        "name": "John Doe",
        "department": "cardiology",
        "admitted_at": "2025-01-01T00:00:00",
    }

    # discharge_patient
    mock.discharge_patient.return_value = {
        "status": "discharged",
        "patient_id": "pat_001",
        "discharged_at": "2025-01-02T00:00:00",
    }

    # list_patients
    mock_patient = MagicMock()
    mock_patient.to_dict.return_value = {
        "patient_id": "pat_001",
        "name": "John Doe",
        "department": "cardiology",
        "status": "admitted",
    }
    mock.list_patients.return_value = [mock_patient]
    mock.get_patient.return_value = mock_patient

    # list_hospitals
    mock.list_hospitals.return_value = [
        {"hospital_id": "hosp_001", "name": "Test Hospital", "status": "active"},
    ]

    # get_stats
    mock.get_stats.return_value = {
        "total_hospitals": 1,
        "total_patients": 1,
        "total_staff": 50,
        "total_beds": 100,
        "occupancy_rate": 0.75,
    }

    return mock


@pytest.fixture
def app(mock_hospital_sector):
    """Create a FastAPI app with only hospital routes and mocked dependencies."""
    app = FastAPI()

    with patch("core.api_endpoints.sector_api._get_hospital",
               return_value=mock_hospital_sector):
        # Import and include the router after patching
        from core.api_endpoints.sector_api import router
        # Only include relevant routes by filtering
        app.include_router(router)
        yield app


@pytest.fixture
def client(app):
    """Test client for the hospital API."""
    return TestClient(app)


# ─── Hospital Registration Tests ─────────────────────────────────────────────


class TestHospitalRegistration:
    """Tests for hospital registration endpoint."""

    def test_register_hospital_success(self, client, mock_hospital_sector):
        """POST /api/sectors/hospital/register creates a hospital."""
        response = client.post("/api/sectors/hospital/register", json={
            "hospital_id": "hosp_001",
            "name": "Test Hospital",
            "address": "123 Main St",
            "phone": "555-0100",
            "email": "info@testhospital.com",
            "department_count": 10,
            "bed_count": 100,
            "staff_count": 50,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["hospital_id"] == "hosp_001"
        assert data["name"] == "Test Hospital"
        mock_hospital_sector.register_hospital.assert_called_once()

    def test_register_hospital_unavailable(self, client):
        """Returns 503 when HospitalSector is not available."""
        with patch("core.api_endpoints.sector_api._get_hospital", return_value=None):
            response = client.post("/api/sectors/hospital/register", json={
                "hospital_id": "hosp_002",
                "name": "Unavailable Hospital",
            })
            assert response.status_code == 503

    def test_register_hospital_minimal(self, client, mock_hospital_sector):
        """Register with only required fields."""
        response = client.post("/api/sectors/hospital/register", json={
            "hospital_id": "hosp_002",
            "name": "Minimal Hospital",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["hospital_id"] == "hosp_001"  # from mock
        mock_hospital_sector.register_hospital.assert_called()


# ─── Patient Admission/Discharge Tests ───────────────────────────────────────


class TestPatientAdmission:
    """Tests for patient admission and discharge."""

    def test_admit_patient_success(self, client, mock_hospital_sector):
        """POST /api/sectors/hospital/admit admits a patient."""
        response = client.post("/api/sectors/hospital/admit", json={
            "patient_id": "pat_001",
            "name": "John Doe",
            "age": 35,
            "gender": "male",
            "blood_type": "A+",
            "diagnosis": "Chest pain",
            "department": "cardiology",
            "hospital_id": "hosp_001",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "admitted"
        assert data["patient_id"] == "pat_001"
        mock_hospital_sector.admit_patient.assert_called_once()

    def test_admit_patient_unavailable(self, client):
        """Returns 503 when HospitalSector is not available."""
        with patch("core.api_endpoints.sector_api._get_hospital", return_value=None):
            response = client.post("/api/sectors/hospital/admit", json={
                "patient_id": "pat_002",
                "name": "Jane Doe",
            })
            assert response.status_code == 503

    def test_discharge_patient_success(self, client, mock_hospital_sector):
        """POST /api/sectors/hospital/discharge/{patient_id} discharges a patient."""
        response = client.post("/api/sectors/hospital/discharge/pat_001")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "discharged"
        assert data["patient_id"] == "pat_001"
        mock_hospital_sector.discharge_patient.assert_called_once_with("pat_001")


# ─── Patient Listing Tests ───────────────────────────────────────────────────


class TestPatientListing:
    """Tests for patient listing and retrieval."""

    def test_list_patients_all(self, client, mock_hospital_sector):
        """GET /api/sectors/hospital/patients lists all patients."""
        response = client.get("/api/sectors/hospital/patients")
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert len(data["patients"]) > 0
        mock_hospital_sector.list_patients.assert_called_once_with(None)

    def test_list_patients_by_department(self, client, mock_hospital_sector):
        """GET /api/sectors/hospital/patients?department=cardiology filters by department."""
        response = client.get("/api/sectors/hospital/patients", params={"department": "cardiology"})
        assert response.status_code == 200
        mock_hospital_sector.list_patients.assert_called_with("cardiology")

    def test_get_patient_by_id(self, client, mock_hospital_sector):
        """GET /api/sectors/hospital/patient/{patient_id} returns patient details."""
        response = client.get("/api/sectors/hospital/patient/pat_001")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "pat_001"
        mock_hospital_sector.get_patient.assert_called_once_with("pat_001")

    def test_get_patient_not_found(self, client, mock_hospital_sector):
        """Returns 404 for non-existent patient."""
        mock_hospital_sector.get_patient.return_value = None
        response = client.get("/api/sectors/hospital/patient/nonexistent")
        assert response.status_code == 404

    def test_list_hospitals(self, client, mock_hospital_sector):
        """GET /api/sectors/hospital/list lists all hospitals."""
        response = client.get("/api/sectors/hospital/list")
        assert response.status_code == 200
        data = response.json()
        assert "hospitals" in data
        assert len(data["hospitals"]) > 0


# ─── Hospital Statistics Tests ───────────────────────────────────────────────


class TestHospitalStats:
    """Tests for hospital statistics endpoint."""

    def test_hospital_stats(self, client, mock_hospital_sector):
        """GET /api/sectors/hospital/stats returns statistics."""
        response = client.get("/api/sectors/hospital/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_hospitals" in data
        assert "total_patients" in data
        assert "occupancy_rate" in data
        mock_hospital_sector.get_stats.assert_called_once()

    def test_hospital_stats_unavailable(self, client):
        """Returns 503 when HospitalSector is not available."""
        with patch("core.api_endpoints.sector_api._get_hospital", return_value=None):
            response = client.get("/api/sectors/hospital/stats")
            assert response.status_code == 503
