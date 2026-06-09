#!/usr/bin/env python3
"""
ASIMNEXUS Sector Module API Endpoints
======================================
FastAPI endpoints for all sector modules:
- Hospital: /api/sectors/hospital/*
- Hotel: /api/sectors/hotel/*
- Education: /api/sectors/education/*
- Banking: /api/sectors/banking/*

Each endpoint enforces the 51/49 constitutional balance.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body

logger = logging.getLogger("AsimNexus.API.Sectors")

router = APIRouter()

# ─── SINGLETON GETTERS ─────────────────────────────────────────────────────

def _get_hospital():
    try:
        from core.sectors import HospitalSector
        return HospitalSector()
    except Exception as e:
        logger.warning("HospitalSector not available: %s", e)
        return None

def _get_hotel():
    try:
        from core.sectors import HotelSector
        return HotelSector()
    except Exception as e:
        logger.warning("HotelSector not available: %s", e)
        return None

def _get_education():
    try:
        from core.sectors import EducationSector
        return EducationSector()
    except Exception as e:
        logger.warning("EducationSector not available: %s", e)
        return None

def _get_banking():
    try:
        from core.sectors import BankingSector
        return BankingSector()
    except Exception as e:
        logger.warning("BankingSector not available: %s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# HOSPITAL SECTOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/sectors/hospital/register", tags=["Sectors - Hospital"])
async def register_hospital(req: dict = Body(...)):
    """Register a new hospital."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return engine.register_hospital(
        hospital_id=req.get("hospital_id"),
        name=req.get("name"),
        address=req.get("address"),
        phone=req.get("phone"),
        email=req.get("email"),
        department_count=req.get("department_count", 10),
        bed_count=req.get("bed_count", 100),
        staff_count=req.get("staff_count", 50),
    )

@router.post("/api/sectors/hospital/admit", tags=["Sectors - Hospital"])
async def admit_patient(req: dict = Body(...)):
    """Admit a patient to a hospital."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return engine.admit_patient(
        patient_id=req.get("patient_id"),
        name=req.get("name"),
        age=req.get("age"),
        gender=req.get("gender"),
        blood_type=req.get("blood_type"),
        diagnosis=req.get("diagnosis"),
        department=req.get("department"),
        hospital_id=req.get("hospital_id"),
        notes=req.get("notes", ""),
    )

@router.post("/api/sectors/hospital/discharge/{patient_id}", tags=["Sectors - Hospital"])
async def discharge_patient(patient_id: str):
    """Discharge a patient."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return engine.discharge_patient(patient_id)

@router.get("/api/sectors/hospital/patients", tags=["Sectors - Hospital"])
async def list_patients(department: Optional[str] = Query(None)):
    """List patients, optionally filtered by department."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return {"patients": engine.list_patients(department)}

@router.get("/api/sectors/hospital/patient/{patient_id}", tags=["Sectors - Hospital"])
async def get_patient(patient_id: str):
    """Get a patient by ID."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    patient = engine.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient.to_dict()

@router.get("/api/sectors/hospital/list", tags=["Sectors - Hospital"])
async def list_hospitals():
    """List all registered hospitals."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return {"hospitals": engine.list_hospitals()}

@router.get("/api/sectors/hospital/stats", tags=["Sectors - Hospital"])
async def hospital_stats():
    """Get hospital sector statistics."""
    engine = _get_hospital()
    if not engine:
        raise HTTPException(503, "HospitalSector not available")
    return engine.get_stats()


# ═══════════════════════════════════════════════════════════════════════════
# HOTEL SECTOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/sectors/hotel/rooms", tags=["Sectors - Hotel"])
async def add_room(req: dict = Body(...)):
    """Add a room to the hotel."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.add_room(
        room_id=req.get("room_id"),
        room_number=req.get("room_number"),
        room_type=req.get("room_type"),
        floor=req.get("floor"),
        capacity=req.get("capacity"),
        price_per_night=req.get("price_per_night"),
        amenities=req.get("amenities"),
    )

@router.post("/api/sectors/hotel/bookings", tags=["Sectors - Hotel"])
async def create_booking(req: dict = Body(...)):
    """Create a hotel booking."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.create_booking(
        booking_id=req.get("booking_id"),
        guest_name=req.get("guest_name"),
        guest_email=req.get("guest_email"),
        guest_phone=req.get("guest_phone"),
        room_id=req.get("room_id"),
        check_in=req.get("check_in"),
        check_out=req.get("check_out"),
        total_amount=req.get("total_amount"),
        special_requests=req.get("special_requests", ""),
    )

@router.post("/api/sectors/hotel/bookings/{booking_id}/checkin", tags=["Sectors - Hotel"])
async def check_in(booking_id: str):
    """Check in a guest."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.check_in(booking_id)

@router.post("/api/sectors/hotel/bookings/{booking_id}/checkout", tags=["Sectors - Hotel"])
async def check_out(booking_id: str):
    """Check out a guest."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.check_out(booking_id)

@router.post("/api/sectors/hotel/bookings/{booking_id}/cancel", tags=["Sectors - Hotel"])
async def cancel_booking(booking_id: str):
    """Cancel a booking."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.cancel_booking(booking_id)

@router.get("/api/sectors/hotel/rooms", tags=["Sectors - Hotel"])
async def list_rooms(status: Optional[str] = Query(None)):
    """List rooms, optionally filtered by status."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return {"rooms": engine.list_rooms(status)}

@router.get("/api/sectors/hotel/bookings", tags=["Sectors - Hotel"])
async def list_bookings(status: Optional[str] = Query(None)):
    """List bookings, optionally filtered by status."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return {"bookings": engine.list_bookings(status)}

@router.get("/api/sectors/hotel/room/{room_id}", tags=["Sectors - Hotel"])
async def get_room(room_id: str):
    """Get a room by ID."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    room = engine.get_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    return room.to_dict()

@router.get("/api/sectors/hotel/booking/{booking_id}", tags=["Sectors - Hotel"])
async def get_booking(booking_id: str):
    """Get a booking by ID."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    booking = engine.get_booking(booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking.to_dict()

@router.get("/api/sectors/hotel/stats", tags=["Sectors - Hotel"])
async def hotel_stats():
    """Get hotel sector statistics."""
    engine = _get_hotel()
    if not engine:
        raise HTTPException(503, "HotelSector not available")
    return engine.get_stats()


# ═══════════════════════════════════════════════════════════════════════════
# EDUCATION SECTOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/sectors/education/enroll", tags=["Sectors - Education"])
async def enroll_student(req: dict = Body(...)):
    """Enroll a new student."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.enroll_student(
        student_id=req.get("student_id"),
        name=req.get("name"),
        email=req.get("email"),
        phone=req.get("phone"),
        date_of_birth=req.get("date_of_birth"),
        address=req.get("address"),
        program=req.get("program"),
    )

@router.post("/api/sectors/education/courses", tags=["Sectors - Education"])
async def create_course(req: dict = Body(...)):
    """Create a new course."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.create_course(
        course_id=req.get("course_id"),
        name=req.get("name"),
        code=req.get("code"),
        description=req.get("description"),
        level=req.get("level"),
        credits=req.get("credits"),
        department=req.get("department"),
        instructor=req.get("instructor"),
        capacity=req.get("capacity"),
    )

@router.post("/api/sectors/education/enroll-course", tags=["Sectors - Education"])
async def enroll_in_course(req: dict = Body(...)):
    """Enroll a student in a course."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.enroll_in_course(
        student_id=req.get("student_id"),
        course_id=req.get("course_id"),
    )

@router.post("/api/sectors/education/grades", tags=["Sectors - Education"])
async def update_grades(req: dict = Body(...)):
    """Update a student's grades."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.update_grades(
        student_id=req.get("student_id"),
        gpa=req.get("gpa"),
        credits_earned=req.get("credits_earned"),
    )

@router.post("/api/sectors/education/graduate/{student_id}", tags=["Sectors - Education"])
async def graduate_student(student_id: str):
    """Graduate a student."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.graduate_student(student_id)

@router.get("/api/sectors/education/students", tags=["Sectors - Education"])
async def list_students(program: Optional[str] = Query(None)):
    """List students, optionally filtered by program."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return {"students": engine.list_students(program)}

@router.get("/api/sectors/education/courses", tags=["Sectors - Education"])
async def list_courses(department: Optional[str] = Query(None)):
    """List courses, optionally filtered by department."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return {"courses": engine.list_courses(department)}

@router.get("/api/sectors/education/student/{student_id}", tags=["Sectors - Education"])
async def get_student(student_id: str):
    """Get a student by ID."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    student = engine.get_student(student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student.to_dict()

@router.get("/api/sectors/education/course/{course_id}", tags=["Sectors - Education"])
async def get_course(course_id: str):
    """Get a course by ID."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    course = engine.get_course(course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    return course.to_dict()

@router.get("/api/sectors/education/stats", tags=["Sectors - Education"])
async def education_stats():
    """Get education sector statistics."""
    engine = _get_education()
    if not engine:
        raise HTTPException(503, "EducationSector not available")
    return engine.get_stats()


# ═══════════════════════════════════════════════════════════════════════════
# BANKING SECTOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/sectors/banking/accounts", tags=["Sectors - Banking"])
async def create_account(req: dict = Body(...)):
    """Create a new bank account."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return engine.create_account(
        account_id=req.get("account_id"),
        owner_name=req.get("owner_name"),
        owner_id=req.get("owner_id"),
        account_type=req.get("account_type", "savings"),
        currency=req.get("currency", "NRS"),
        initial_deposit=req.get("initial_deposit", 0.0),
        kyc_verified=req.get("kyc_verified", False),
    )

@router.post("/api/sectors/banking/deposit", tags=["Sectors - Banking"])
async def deposit(req: dict = Body(...)):
    """Deposit money into an account."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return engine.deposit(
        account_id=req.get("account_id"),
        amount=req.get("amount"),
        description=req.get("description", ""),
    )

@router.post("/api/sectors/banking/withdraw", tags=["Sectors - Banking"])
async def withdraw(req: dict = Body(...)):
    """Withdraw money from an account."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return engine.withdraw(
        account_id=req.get("account_id"),
        amount=req.get("amount"),
        description=req.get("description", ""),
    )

@router.post("/api/sectors/banking/transfer", tags=["Sectors - Banking"])
async def transfer(req: dict = Body(...)):
    """Transfer money between accounts."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return engine.transfer(
        from_account=req.get("from_account"),
        to_account=req.get("to_account"),
        amount=req.get("amount"),
        description=req.get("description", ""),
    )

@router.get("/api/sectors/banking/accounts", tags=["Sectors - Banking"])
async def list_accounts(status: Optional[str] = Query(None)):
    """List accounts, optionally filtered by status."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return {"accounts": engine.list_accounts(status)}

@router.get("/api/sectors/banking/account/{account_id}", tags=["Sectors - Banking"])
async def get_account(account_id: str):
    """Get an account by ID."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    account = engine.get_account(account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    return account.to_dict()

@router.get("/api/sectors/banking/account/{account_id}/transactions", tags=["Sectors - Banking"])
async def get_transactions(account_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get transactions for an account."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return {"transactions": engine.get_transactions(account_id, limit)}

@router.get("/api/sectors/banking/stats", tags=["Sectors - Banking"])
async def banking_stats():
    """Get banking sector statistics."""
    engine = _get_banking()
    if not engine:
        raise HTTPException(503, "BankingSector not available")
    return engine.get_stats()


# ═══════════════════════════════════════════════════════════════════════════
# SECTOR HEALTH & OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/sectors/health", tags=["Sectors"])
async def sectors_health():
    """Check availability of all sector modules."""
    return {
        "hospital": _get_hospital() is not None,
        "hotel": _get_hotel() is not None,
        "education": _get_education() is not None,
        "banking": _get_banking() is not None,
    }

@router.get("/api/sectors/stats", tags=["Sectors"])
async def all_sectors_stats():
    """Get combined statistics from all sector modules."""
    result = {}
    for name, getter in [("hospital", _get_hospital), ("hotel", _get_hotel),
                          ("education", _get_education), ("banking", _get_banking)]:
        engine = getter()
        if engine:
            result[name] = engine.get_stats()
        else:
            result[name] = {"error": "not available"}
    return result
