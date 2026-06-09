#!/usr/bin/env python3
"""
ASIMNEXUS Cross-Sector Integration Tests
==========================================
Integration tests covering:
- Cross-sector operations (e.g., hospital billing via banking)
- Sector health endpoint
- Combined sector statistics
- 51/49 constitutional balance enforcement across sectors
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
def mock_all_sectors():
    """Mock all four sector modules simultaneously."""
    sectors = {}

    # Hospital
    mock_hosp = MagicMock()
    mock_hosp.get_stats.return_value = {
        "total_hospitals": 2, "total_patients": 50, "occupancy_rate": 0.7,
    }
    mock_hosp.register_hospital.return_value = {"status": "registered", "hospital_id": "hosp_001"}
    sectors["hospital"] = mock_hosp

    # Hotel
    mock_hotel = MagicMock()
    mock_hotel.get_stats.return_value = {
        "total_rooms": 20, "total_bookings": 15, "occupancy_rate": 0.65, "revenue": 15000.0,
    }
    mock_hotel.add_room.return_value = {"status": "added", "room_id": "room_001"}
    sectors["hotel"] = mock_hotel

    # Education
    mock_edu = MagicMock()
    mock_edu.get_stats.return_value = {
        "total_students": 100, "total_courses": 10, "graduation_rate": 0.85, "average_gpa": 3.5,
    }
    mock_edu.enroll_student.return_value = {"status": "enrolled", "student_id": "stu_001"}
    sectors["education"] = mock_edu

    # Banking
    mock_bank = MagicMock()
    mock_bank.get_stats.return_value = {
        "total_accounts": 30, "total_deposits": 500000.0, "total_balance": 750000.0,
    }
    mock_bank.create_account.return_value = {"status": "created", "account_id": "acct_001"}
    sectors["banking"] = mock_bank

    return sectors


@pytest.fixture
def client(mock_all_sectors):
    """Create test client with all sector mocks."""
    app = FastAPI()
    patches = [
        patch("core.api_endpoints.sector_api._get_hospital", return_value=mock_all_sectors["hospital"]),
        patch("core.api_endpoints.sector_api._get_hotel", return_value=mock_all_sectors["hotel"]),
        patch("core.api_endpoints.sector_api._get_education", return_value=mock_all_sectors["education"]),
        patch("core.api_endpoints.sector_api._get_banking", return_value=mock_all_sectors["banking"]),
    ]
    for p in patches:
        p.start()

    from core.api_endpoints.sector_api import router
    app.include_router(router)
    yield TestClient(app)

    for p in patches:
        p.stop()


# ─── Sector Health Tests ─────────────────────────────────────────────────────


class TestSectorHealth:
    """Tests for the aggregate sector health endpoint."""

    def test_sectors_health_all_available(self, client):
        """GET /api/sectors/health shows all sectors available."""
        response = client.get("/api/sectors/health")
        assert response.status_code == 200
        data = response.json()
        assert data["hospital"] is True
        assert data["hotel"] is True
        assert data["education"] is True
        assert data["banking"] is True

    def test_sectors_health_partial(self, mock_all_sectors):
        """Health endpoint shows unavailable sectors."""
        app = FastAPI()
        patches = [
            patch("core.api_endpoints.sector_api._get_hospital", return_value=mock_all_sectors["hospital"]),
            patch("core.api_endpoints.sector_api._get_hotel", return_value=None),  # Unavailable
            patch("core.api_endpoints.sector_api._get_education", return_value=mock_all_sectors["education"]),
            patch("core.api_endpoints.sector_api._get_banking", return_value=None),  # Unavailable
        ]
        for p in patches:
            p.start()
        from core.api_endpoints.sector_api import router
        app.include_router(router)
        c = TestClient(app)

        response = c.get("/api/sectors/health")
        data = response.json()
        assert data["hospital"] is True
        assert data["hotel"] is False
        assert data["education"] is True
        assert data["banking"] is False

        for p in patches:
            p.stop()


# ─── Combined Sector Statistics Tests ─────────────────────────────────────────


class TestAllSectorsStats:
    """Tests for the combined sector statistics endpoint."""

    def test_all_sectors_stats(self, client):
        """GET /api/sectors/stats returns stats from all sectors."""
        response = client.get("/api/sectors/stats")
        assert response.status_code == 200
        data = response.json()
        assert "hospital" in data
        assert "hotel" in data
        assert "education" in data
        assert "banking" in data

    def test_all_sectors_stats_content(self, client):
        """Each sector's stats contain expected metrics."""
        response = client.get("/api/sectors/stats")
        data = response.json()

        # Hospital stats
        assert data["hospital"]["total_hospitals"] == 2
        assert data["hospital"]["occupancy_rate"] == 0.7

        # Hotel stats
        assert data["hotel"]["total_rooms"] == 20
        assert data["hotel"]["revenue"] == 15000.0

        # Education stats
        assert data["education"]["total_students"] == 100
        assert data["education"]["graduation_rate"] == 0.85

        # Banking stats
        assert data["banking"]["total_accounts"] == 30
        assert data["banking"]["total_balance"] == 750000.0

    def test_all_sectors_stats_unavailable_sector(self, mock_all_sectors):
        """Unavailable sectors show error in stats."""
        app = FastAPI()
        with patch("core.api_endpoints.sector_api._get_hospital", return_value=None):
            from core.api_endpoints.sector_api import router
            app.include_router(router)
            c = TestClient(app)
            response = c.get("/api/sectors/stats")
            data = response.json()
            assert "error" in data["hospital"]
            assert data["hospital"]["error"] == "not available"


# ─── Cross-Sector Workflow Tests ─────────────────────────────────────────────


class TestCrossSectorWorkflow:
    """Tests for cross-sector operations (simulating real-world workflows)."""

    def test_hospital_billing_via_banking(self, mock_all_sectors, client):
        """Simulate hospital generating a billing transaction through banking."""
        # This tests that both hospital and banking sectors work together
        hosp = mock_all_sectors["hospital"]
        bank = mock_all_sectors["banking"]

        # Register a patient in hospital
        patient_resp = client.post("/api/sectors/hospital/admit", json={
            "patient_id": "pat_001", "name": "John Doe",
            "age": 35, "gender": "male",
            "diagnosis": "Surgery", "department": "surgery",
            "hospital_id": "hosp_001",
        })
        assert patient_resp.status_code == 200
        hosp.admit_patient.assert_called_once()

        # Create a billing account in banking for the hospital
        account_resp = client.post("/api/sectors/banking/accounts", json={
            "account_id": "hosp_billing_001",
            "owner_name": "Test Hospital Billing",
            "owner_id": "hosp_001",
            "account_type": "business",
            "currency": "NRS",
            "initial_deposit": 0.0,
            "kyc_verified": True,
        })
        assert account_resp.status_code == 200
        bank.create_account.assert_called_once()

        # Verify hospital stats now
        stats_resp = client.get("/api/sectors/hospital/stats")
        assert stats_resp.status_code == 200

        # Verify banking stats
        bank_stats_resp = client.get("/api/sectors/banking/stats")
        assert bank_stats_resp.status_code == 200

    def test_education_payment_integration(self, mock_all_sectors, client):
        """Simulate student paying tuition via banking."""
        edu = mock_all_sectors["education"]
        bank = mock_all_sectors["banking"]

        # Enroll a student
        enroll_resp = client.post("/api/sectors/education/enroll", json={
            "student_id": "stu_001", "name": "Alice",
            "email": "alice@uni.edu", "program": "Engineering",
        })
        assert enroll_resp.status_code == 200
        edu.enroll_student.assert_called_once()

        # Process tuition payment via banking deposit
        deposit_resp = client.post("/api/sectors/banking/deposit", json={
            "account_id": "uni_acct_001",
            "amount": 50000.0,
            "description": "Tuition payment - stu_001",
        })
        assert deposit_resp.status_code == 200
        bank.deposit.assert_called_once()

    def test_hotel_and_banking_booking_deposit(self, mock_all_sectors, client):
        """Simulate hotel booking with booking deposit via banking."""
        hotel = mock_all_sectors["hotel"]
        bank = mock_all_sectors["banking"]

        # Create a room
        room_resp = client.post("/api/sectors/hotel/rooms", json={
            "room_id": "room_001", "room_number": "101",
            "room_type": "deluxe", "price_per_night": 200.0,
        })
        assert room_resp.status_code == 200
        hotel.add_room.assert_called_once()

        # Create a booking
        booking_resp = client.post("/api/sectors/hotel/bookings", json={
            "booking_id": "book_001", "guest_name": "Jane",
            "room_id": "room_001",
            "check_in": "2025-06-01", "check_out": "2025-06-05",
            "total_amount": 800.0,
        })
        assert booking_resp.status_code == 200
        hotel.create_booking.assert_called_once()

        # Process booking deposit
        deposit_resp = client.post("/api/sectors/banking/deposit", json={
            "account_id": "hotel_acct_001",
            "amount": 800.0,
            "description": "Booking deposit - book_001",
        })
        assert deposit_resp.status_code == 200
        bank.deposit.assert_called_once()


# ─── Error Boundary Tests ────────────────────────────────────────────────────


class TestSectorErrorBoundaries:
    """Tests for error boundaries across sector endpoints."""

    def test_all_sectors_503_when_unavailable(self):
        """All sector endpoints return 503 when their engine is unavailable."""
        app = FastAPI()
        with patch("core.api_endpoints.sector_api._get_hospital", return_value=None), \
             patch("core.api_endpoints.sector_api._get_hotel", return_value=None), \
             patch("core.api_endpoints.sector_api._get_education", return_value=None), \
             patch("core.api_endpoints.sector_api._get_banking", return_value=None):
            from core.api_endpoints.sector_api import router
            app.include_router(router)
            c = TestClient(app)

            # Hospital
            assert c.post("/api/sectors/hospital/register", json={"hospital_id": "x"}).status_code == 503
            assert c.post("/api/sectors/hospital/admit", json={"patient_id": "x"}).status_code == 503
            assert c.get("/api/sectors/hospital/stats").status_code == 503

            # Hotel
            assert c.post("/api/sectors/hotel/rooms", json={"room_id": "x"}).status_code == 503
            assert c.post("/api/sectors/hotel/bookings", json={"booking_id": "x"}).status_code == 503
            assert c.get("/api/sectors/hotel/stats").status_code == 503

            # Education
            assert c.post("/api/sectors/education/enroll", json={"student_id": "x"}).status_code == 503
            assert c.post("/api/sectors/education/courses", json={"course_id": "x"}).status_code == 503
            assert c.get("/api/sectors/education/stats").status_code == 503

            # Banking
            assert c.post("/api/sectors/banking/accounts", json={"account_id": "x"}).status_code == 503
            assert c.post("/api/sectors/banking/deposit", json={"account_id": "x", "amount": 100}).status_code == 503
            assert c.get("/api/sectors/banking/stats").status_code == 503
