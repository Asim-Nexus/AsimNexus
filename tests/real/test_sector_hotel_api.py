#!/usr/bin/env python3
"""
ASIMNEXUS Hotel Sector API Tests
==================================
Tests for all hotel sector endpoints: room management, booking lifecycle,
check-in/check-out, cancellations, and statistics.
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
def mock_hotel_sector():
    """Mock HotelSector with realistic return values."""
    mock = MagicMock()

    mock.add_room.return_value = {
        "status": "added",
        "room_id": "room_001",
        "room_number": "101",
        "room_type": "deluxe",
        "price_per_night": 200.0,
    }

    mock.create_booking.return_value = {
        "status": "created",
        "booking_id": "book_001",
        "guest_name": "Jane Guest",
        "room_id": "room_001",
        "check_in": "2025-06-01",
        "check_out": "2025-06-05",
        "total_amount": 800.0,
    }

    mock.check_in.return_value = {
        "status": "checked_in",
        "booking_id": "book_001",
        "checked_in_at": "2025-06-01T14:00:00",
    }

    mock.check_out.return_value = {
        "status": "checked_out",
        "booking_id": "book_001",
        "checked_out_at": "2025-06-05T11:00:00",
    }

    mock.cancel_booking.return_value = {
        "status": "cancelled",
        "booking_id": "book_001",
        "cancelled_at": "2025-06-01T10:00:00",
    }

    mock_room = MagicMock()
    mock_room.to_dict.return_value = {
        "room_id": "room_001",
        "room_number": "101",
        "room_type": "deluxe",
        "status": "available",
        "price_per_night": 200.0,
    }
    mock.get_room.return_value = mock_room

    mock_booking = MagicMock()
    mock_booking.to_dict.return_value = {
        "booking_id": "book_001",
        "guest_name": "Jane Guest",
        "room_id": "room_001",
        "status": "active",
    }
    mock.get_booking.return_value = mock_booking

    mock.list_rooms.return_value = [mock_room]
    mock.list_bookings.return_value = [mock_booking]

    mock.get_stats.return_value = {
        "total_rooms": 1,
        "total_bookings": 1,
        "occupancy_rate": 0.75,
        "average_daily_rate": 200.0,
        "revenue": 800.0,
    }

    return mock


@pytest.fixture
def client(mock_hotel_sector):
    """Create test client with mocked hotel sector."""
    app = FastAPI()
    with patch("core.api_endpoints.sector_api._get_hotel",
               return_value=mock_hotel_sector):
        from core.api_endpoints.sector_api import router
        app.include_router(router)
        yield TestClient(app)


# ─── Room Management Tests ───────────────────────────────────────────────────


class TestHotelRoomManagement:
    """Tests for hotel room management endpoints."""

    def test_add_room_success(self, client, mock_hotel_sector):
        """POST /api/sectors/hotel/rooms adds a new room."""
        response = client.post("/api/sectors/hotel/rooms", json={
            "room_id": "room_001",
            "room_number": "101",
            "room_type": "deluxe",
            "floor": 1,
            "capacity": 2,
            "price_per_night": 200.0,
            "amenities": ["wifi", "tv", "minibar"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "added"
        assert data["room_id"] == "room_001"
        mock_hotel_sector.add_room.assert_called_once()

    def test_add_room_unavailable(self, client):
        """Returns 503 when HotelSector is not available."""
        with patch("core.api_endpoints.sector_api._get_hotel", return_value=None):
            response = client.post("/api/sectors/hotel/rooms", json={
                "room_id": "room_002",
                "room_number": "102",
            })
            assert response.status_code == 503

    def test_list_rooms(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/rooms lists all rooms."""
        response = client.get("/api/sectors/hotel/rooms")
        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        assert len(data["rooms"]) > 0
        mock_hotel_sector.list_rooms.assert_called_once_with(None)

    def test_list_rooms_by_status(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/rooms?status=available filters by status."""
        response = client.get("/api/sectors/hotel/rooms", params={"status": "available"})
        assert response.status_code == 200
        mock_hotel_sector.list_rooms.assert_called_with("available")

    def test_get_room_by_id(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/room/{room_id} returns room details."""
        response = client.get("/api/sectors/hotel/room/room_001")
        assert response.status_code == 200
        data = response.json()
        assert data["room_id"] == "room_001"
        mock_hotel_sector.get_room.assert_called_once_with("room_001")

    def test_get_room_not_found(self, client, mock_hotel_sector):
        """Returns 404 for non-existent room."""
        mock_hotel_sector.get_room.return_value = None
        response = client.get("/api/sectors/hotel/room/nonexistent")
        assert response.status_code == 404


# ─── Booking Lifecycle Tests ────────────────────────────────────────────────


class TestHotelBookingLifecycle:
    """Tests for the full hotel booking lifecycle."""

    def test_create_booking_success(self, client, mock_hotel_sector):
        """POST /api/sectors/hotel/bookings creates a booking."""
        response = client.post("/api/sectors/hotel/bookings", json={
            "booking_id": "book_001",
            "guest_name": "Jane Guest",
            "guest_email": "jane@example.com",
            "guest_phone": "555-0200",
            "room_id": "room_001",
            "check_in": "2025-06-01",
            "check_out": "2025-06-05",
            "total_amount": 800.0,
            "special_requests": "Extra pillows",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["booking_id"] == "book_001"
        mock_hotel_sector.create_booking.assert_called_once()

    def test_check_in_success(self, client, mock_hotel_sector):
        """POST /api/sectors/hotel/bookings/{id}/checkin checks in a guest."""
        response = client.post("/api/sectors/hotel/bookings/book_001/checkin")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "checked_in"
        mock_hotel_sector.check_in.assert_called_once_with("book_001")

    def test_check_out_success(self, client, mock_hotel_sector):
        """POST /api/sectors/hotel/bookings/{id}/checkout checks out a guest."""
        response = client.post("/api/sectors/hotel/bookings/book_001/checkout")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "checked_out"
        mock_hotel_sector.check_out.assert_called_once_with("book_001")

    def test_cancel_booking_success(self, client, mock_hotel_sector):
        """POST /api/sectors/hotel/bookings/{id}/cancel cancels a booking."""
        response = client.post("/api/sectors/hotel/bookings/book_001/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        mock_hotel_sector.cancel_booking.assert_called_once_with("book_001")

    def test_list_bookings(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/bookings lists all bookings."""
        response = client.get("/api/sectors/hotel/bookings")
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        mock_hotel_sector.list_bookings.assert_called_once_with(None)

    def test_get_booking_by_id(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/booking/{id} returns booking details."""
        response = client.get("/api/sectors/hotel/booking/book_001")
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == "book_001"
        mock_hotel_sector.get_booking.assert_called_once_with("book_001")

    def test_get_booking_not_found(self, client, mock_hotel_sector):
        """Returns 404 for non-existent booking."""
        mock_hotel_sector.get_booking.return_value = None
        response = client.get("/api/sectors/hotel/booking/nonexistent")
        assert response.status_code == 404


# ─── Hotel Statistics Tests ──────────────────────────────────────────────────


class TestHotelStats:
    """Tests for hotel statistics endpoint."""

    def test_hotel_stats(self, client, mock_hotel_sector):
        """GET /api/sectors/hotel/stats returns statistics."""
        response = client.get("/api/sectors/hotel/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_rooms" in data
        assert "occupancy_rate" in data
        assert "revenue" in data
        mock_hotel_sector.get_stats.assert_called_once()

    def test_hotel_stats_unavailable(self, client):
        """Returns 503 when HotelSector is not available."""
        with patch("core.api_endpoints.sector_api._get_hotel", return_value=None):
            response = client.get("/api/sectors/hotel/stats")
            assert response.status_code == 503
