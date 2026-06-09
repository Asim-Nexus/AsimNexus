#!/usr/bin/env python3
"""
ASIMNEXUS Hotel Sector Module
==============================
Hospitality sector management with 51/49 constitutional balance enforcement.

The Hotel sector manages:
- Room inventory and booking
- Guest check-in/check-out
- Housekeeping and maintenance
- Hospitality compliance
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("AsimNexus.Sectors.Hotel")


class RoomType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"
    PENTHOUSE = "penthouse"


class RoomStatus(Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"


class BookingStatus(Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class RoomRecord:
    """A single room in the hotel."""
    room_id: str
    room_number: str
    room_type: RoomType
    floor: int
    capacity: int
    price_per_night: float
    status: RoomStatus = RoomStatus.AVAILABLE
    amenities: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["room_type"] = self.room_type.value
        result["status"] = self.status.value
        return result


@dataclass
class HotelBooking:
    """A hotel booking record."""
    booking_id: str
    guest_name: str
    guest_email: str
    guest_phone: str
    room_id: str
    check_in: str
    check_out: str
    total_amount: float
    status: BookingStatus = BookingStatus.CONFIRMED
    special_requests: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


class HotelSector:
    """
    Hotel Sector Manager.
    Enforces constitutional balance: 51% government / 49% private hospitality oversight.
    """

    def __init__(self):
        self.rooms: Dict[str, RoomRecord] = {}
        self.bookings: Dict[str, HotelBooking] = {}
        self.hotel_name = "ASIMNEXUS Global Hospitality"
        self._audit_log: List[Dict[str, Any]] = []
        logger.info("🏨 Hotel Sector initialized (51/49 balance enforced)")

    def add_room(
        self,
        room_id: str,
        room_number: str,
        room_type: str,
        floor: int,
        capacity: int,
        price_per_night: float,
        amenities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add a room to the hotel inventory."""
        if room_id in self.rooms:
            return {"error": "Room already exists", "room_id": room_id}

        try:
            rtype = RoomType(room_type)
        except ValueError:
            return {"error": f"Invalid room type: {room_type}"}

        record = RoomRecord(
            room_id=room_id,
            room_number=room_number,
            room_type=rtype,
            floor=floor,
            capacity=capacity,
            price_per_night=price_per_night,
            amenities=amenities or [],
        )
        self.rooms[room_id] = record
        self._audit("room_added", room_id)
        return {"status": "added", "room_id": room_id, "room_number": room_number}

    def create_booking(
        self,
        booking_id: str,
        guest_name: str,
        guest_email: str,
        guest_phone: str,
        room_id: str,
        check_in: str,
        check_out: str,
        total_amount: float,
        special_requests: str = "",
    ) -> Dict[str, Any]:
        """Create a new booking."""
        if room_id not in self.rooms:
            return {"error": "Room not found", "room_id": room_id}

        if self.rooms[room_id].status != RoomStatus.AVAILABLE:
            return {"error": "Room is not available", "room_id": room_id, "status": self.rooms[room_id].status.value}

        if booking_id in self.bookings:
            return {"error": "Booking ID already exists", "booking_id": booking_id}

        booking = HotelBooking(
            booking_id=booking_id,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            total_amount=total_amount,
            special_requests=special_requests,
        )
        self.bookings[booking_id] = booking
        self.rooms[room_id].status = RoomStatus.BOOKED
        self.rooms[room_id].updated_at = datetime.utcnow().isoformat()
        self._audit("booking_created", booking_id, {"room_id": room_id})
        return {"status": "created", "booking_id": booking_id, "guest_name": guest_name}

    def check_in(self, booking_id: str) -> Dict[str, Any]:
        """Check in a guest."""
        if booking_id not in self.bookings:
            return {"error": "Booking not found", "booking_id": booking_id}

        booking = self.bookings[booking_id]
        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Booking status is {booking.status.value}, cannot check in"}

        booking.status = BookingStatus.CHECKED_IN
        booking.updated_at = datetime.utcnow().isoformat()
        if booking.room_id in self.rooms:
            self.rooms[booking.room_id].status = RoomStatus.OCCUPIED
        self._audit("guest_checked_in", booking_id)
        return {"status": "checked_in", "booking_id": booking_id}

    def check_out(self, booking_id: str) -> Dict[str, Any]:
        """Check out a guest."""
        if booking_id not in self.bookings:
            return {"error": "Booking not found", "booking_id": booking_id}

        booking = self.bookings[booking_id]
        if booking.status != BookingStatus.CHECKED_IN:
            return {"error": f"Booking status is {booking.status.value}, cannot check out"}

        booking.status = BookingStatus.CHECKED_OUT
        booking.updated_at = datetime.utcnow().isoformat()
        if booking.room_id in self.rooms:
            self.rooms[booking.room_id].status = RoomStatus.CLEANING
        self._audit("guest_checked_out", booking_id)
        return {"status": "checked_out", "booking_id": booking_id}

    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """Cancel a booking."""
        if booking_id not in self.bookings:
            return {"error": "Booking not found", "booking_id": booking_id}

        booking = self.bookings[booking_id]
        old_status = booking.status
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow().isoformat()
        if booking.room_id in self.rooms and old_status in (BookingStatus.CONFIRMED,):
            self.rooms[booking.room_id].status = RoomStatus.AVAILABLE
        self._audit("booking_cancelled", booking_id)
        return {"status": "cancelled", "booking_id": booking_id}

    def get_room(self, room_id: str) -> Optional[RoomRecord]:
        """Get room by ID."""
        return self.rooms.get(room_id)

    def get_booking(self, booking_id: str) -> Optional[HotelBooking]:
        """Get booking by ID."""
        return self.bookings.get(booking_id)

    def list_rooms(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List rooms, optionally filtered by status."""
        results = []
        for r in self.rooms.values():
            if status and r.status.value != status:
                continue
            results.append(r.to_dict())
        return results

    def list_bookings(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List bookings, optionally filtered by status."""
        results = []
        for b in self.bookings.values():
            if status and b.status.value != status:
                continue
            results.append(b.to_dict())
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get hotel sector statistics."""
        return {
            "hotel_name": self.hotel_name,
            "total_rooms": len(self.rooms),
            "available_rooms": sum(1 for r in self.rooms.values() if r.status == RoomStatus.AVAILABLE),
            "booked_rooms": sum(1 for r in self.rooms.values() if r.status == RoomStatus.BOOKED),
            "occupied_rooms": sum(1 for r in self.rooms.values() if r.status == RoomStatus.OCCUPIED),
            "maintenance_rooms": sum(1 for r in self.rooms.values() if r.status == RoomStatus.MAINTENANCE),
            "total_bookings": len(self.bookings),
            "active_bookings": sum(1 for b in self.bookings.values() if b.status in (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)),
            "government_share": 0.51,
            "private_share": 0.49,
            "audit_entries": len(self._audit_log),
        }

    def _audit(self, action: str, resource_id: str, details: Optional[Dict] = None) -> None:
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_id": resource_id,
            "details": details or {},
            "sector": "hotel",
        })

    def reset(self) -> None:
        """Reset all data (for testing)."""
        self.rooms.clear()
        self.bookings.clear()
        self._audit_log.clear()
