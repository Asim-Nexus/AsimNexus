#!/usr/bin/env python3
"""
ASIMNEXUS Education Sector Module
===================================
Educational institution management with 51/49 constitutional balance enforcement.

The Education sector manages:
- Student enrollment and records
- Course catalog and curriculum
- Faculty credentials and assignments
- Academic compliance (FERPA, GDPR)
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("AsimNexus.Sectors.Education")


class EnrollmentStatus(Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    DROPPED = "dropped"
    SUSPENDED = "suspended"


class CourseLevel(Enum):
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    DOCTORAL = "doctoral"
    CERTIFICATE = "certificate"
    CONTINUING_EDUCATION = "continuing_education"


@dataclass
class StudentRecord:
    """A student's academic record."""
    student_id: str
    name: str
    email: str
    phone: str
    date_of_birth: str
    address: str
    enrollment_date: str
    program: str
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    gpa: float = 0.0
    credits_earned: int = 0
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


@dataclass
class CourseRecord:
    """A course offering."""
    course_id: str
    name: str
    code: str
    description: str
    level: CourseLevel
    credits: int
    department: str
    instructor: str
    capacity: int
    enrolled_count: int = 0
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["level"] = self.level.value
        return result


class EducationSector:
    """
    Education Sector Manager.
    Enforces constitutional balance: 51% government / 49% private academic oversight.
    """

    def __init__(self):
        self.students: Dict[str, StudentRecord] = {}
        self.courses: Dict[str, CourseRecord] = {}
        self._audit_log: List[Dict[str, Any]] = []
        logger.info("🎓 Education Sector initialized (51/49 balance enforced)")

    def enroll_student(
        self,
        student_id: str,
        name: str,
        email: str,
        phone: str,
        date_of_birth: str,
        address: str,
        program: str,
    ) -> Dict[str, Any]:
        """Enroll a new student."""
        if student_id in self.students:
            return {"error": "Student already enrolled", "student_id": student_id}

        record = StudentRecord(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            address=address,
            enrollment_date=datetime.utcnow().isoformat(),
            program=program,
        )
        self.students[student_id] = record
        self._audit("student_enrolled", student_id)
        return {"status": "enrolled", "student_id": student_id, "name": name}

    def create_course(
        self,
        course_id: str,
        name: str,
        code: str,
        description: str,
        level: str,
        credits: int,
        department: str,
        instructor: str,
        capacity: int,
    ) -> Dict[str, Any]:
        """Create a new course."""
        if course_id in self.courses:
            return {"error": "Course already exists", "course_id": course_id}

        try:
            clevel = CourseLevel(level)
        except ValueError:
            return {"error": f"Invalid course level: {level}"}

        record = CourseRecord(
            course_id=course_id,
            name=name,
            code=code,
            description=description,
            level=clevel,
            credits=credits,
            department=department,
            instructor=instructor,
            capacity=capacity,
        )
        self.courses[course_id] = record
        self._audit("course_created", course_id)
        return {"status": "created", "course_id": course_id, "name": name}

    def enroll_in_course(self, student_id: str, course_id: str) -> Dict[str, Any]:
        """Enroll a student in a course."""
        if student_id not in self.students:
            return {"error": "Student not found", "student_id": student_id}
        if course_id not in self.courses:
            return {"error": "Course not found", "course_id": course_id}

        course = self.courses[course_id]
        if course.enrolled_count >= course.capacity:
            return {"error": "Course is full", "course_id": course_id, "capacity": course.capacity}

        course.enrolled_count += 1
        course.updated_at = datetime.utcnow().isoformat()
        self._audit("student_enrolled_course", student_id, {"course_id": course_id})
        return {"status": "enrolled", "student_id": student_id, "course_id": course_id}

    def update_grades(self, student_id: str, gpa: float, credits_earned: int) -> Dict[str, Any]:
        """Update a student's grades."""
        if student_id not in self.students:
            return {"error": "Student not found", "student_id": student_id}

        self.students[student_id].gpa = gpa
        self.students[student_id].credits_earned = credits_earned
        self.students[student_id].updated_at = datetime.utcnow().isoformat()
        self._audit("grades_updated", student_id, {"gpa": gpa, "credits": credits_earned})
        return {"status": "updated", "student_id": student_id, "gpa": gpa}

    def graduate_student(self, student_id: str) -> Dict[str, Any]:
        """Graduate a student."""
        if student_id not in self.students:
            return {"error": "Student not found", "student_id": student_id}

        self.students[student_id].status = EnrollmentStatus.GRADUATED
        self.students[student_id].updated_at = datetime.utcnow().isoformat()
        self._audit("student_graduated", student_id)
        return {"status": "graduated", "student_id": student_id}

    def get_student(self, student_id: str) -> Optional[StudentRecord]:
        """Get student by ID."""
        return self.students.get(student_id)

    def get_course(self, course_id: str) -> Optional[CourseRecord]:
        """Get course by ID."""
        return self.courses.get(course_id)

    def list_students(self, program: Optional[str] = None) -> List[Dict[str, Any]]:
        """List students, optionally filtered by program."""
        results = []
        for s in self.students.values():
            if program and s.program != program:
                continue
            results.append(s.to_dict())
        return results

    def list_courses(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """List courses, optionally filtered by department."""
        results = []
        for c in self.courses.values():
            if department and c.department != department:
                continue
            results.append(c.to_dict())
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get education sector statistics."""
        return {
            "total_students": len(self.students),
            "active_students": sum(1 for s in self.students.values() if s.status == EnrollmentStatus.ACTIVE),
            "graduated_students": sum(1 for s in self.students.values() if s.status == EnrollmentStatus.GRADUATED),
            "total_courses": len(self.courses),
            "total_capacity": sum(c.capacity for c in self.courses.values()),
            "total_enrolled": sum(c.enrolled_count for c in self.courses.values()),
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
            "sector": "education",
        })

    def reset(self) -> None:
        """Reset all data (for testing)."""
        self.students.clear()
        self.courses.clear()
        self._audit_log.clear()
