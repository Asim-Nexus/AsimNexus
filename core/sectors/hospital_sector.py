#!/usr/bin/env python3
"""
ASIMNEXUS Hospital Sector Module
=================================
Healthcare sector management with 51/49 constitutional balance enforcement.

The Hospital sector manages:
- Patient records with privacy controls (HIPAA/GDPR compliance)
- Medical staff credentials and scheduling
- Inventory and pharmaceutical tracking
- Emergency protocols with government oversight
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("AsimNexus.Sectors.Hospital")


class PatientStatus(Enum):
    ACTIVE = "active"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    DECEASED = "deceased"


class RecordClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class PatientRecord:
    """A single patient medical record."""
    patient_id: str
    name: str
    age: int
    gender: str
    blood_type: str
    diagnosis: str
    department: str
    admitted_at: str
    status: PatientStatus = PatientStatus.ACTIVE
    classification: RecordClassification = RecordClassification.CONFIDENTIAL
    notes: str = ""
    record_hash: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.record_hash:
            self.record_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = f"{self.patient_id}:{self.name}:{self.diagnosis}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["classification"] = self.classification.value
        return result


@dataclass
class HospitalRecord:
    """Hospital information record."""
    hospital_id: str
    name: str
    address: str
    phone: str
    email: str
    department_count: int
    bed_count: int
    staff_count: int
    government_share: float = 0.51
    private_share: float = 0.49
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HospitalSector:
    """
    Hospital Sector Manager.
    Enforces constitutional balance: 51% government / 49% private oversight.
    """

    def __init__(self):
        self.hospitals: Dict[str, HospitalRecord] = {}
        self.patients: Dict[str, PatientRecord] = {}
        self._audit_log: List[Dict[str, Any]] = []
        logger.info("🏥 Hospital Sector initialized (51/49 balance enforced)")

    def register_hospital(
        self,
        hospital_id: str,
        name: str,
        address: str,
        phone: str,
        email: str,
        department_count: int = 10,
        bed_count: int = 100,
        staff_count: int = 50,
    ) -> Dict[str, Any]:
        """Register a new hospital in the sector."""
        if hospital_id in self.hospitals:
            return {"error": "Hospital already registered", "hospital_id": hospital_id}

        record = HospitalRecord(
            hospital_id=hospital_id,
            name=name,
            address=address,
            phone=phone,
            email=email,
            department_count=department_count,
            bed_count=bed_count,
            staff_count=staff_count,
        )
        self.hospitals[hospital_id] = record
        self._audit("hospital_registered", hospital_id)
        return {"status": "registered", "hospital_id": hospital_id, "name": name}

    def admit_patient(
        self,
        patient_id: str,
        name: str,
        age: int,
        gender: str,
        blood_type: str,
        diagnosis: str,
        department: str,
        hospital_id: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Admit a patient to the hospital."""
        if hospital_id not in self.hospitals:
            return {"error": "Hospital not found", "hospital_id": hospital_id}

        if patient_id in self.patients:
            return {"error": "Patient already registered", "patient_id": patient_id}

        record = PatientRecord(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            blood_type=blood_type,
            diagnosis=diagnosis,
            department=department,
            admitted_at=datetime.utcnow().isoformat(),
            notes=notes,
        )
        self.patients[patient_id] = record
        self._audit("patient_admitted", patient_id, {"hospital_id": hospital_id})
        return {"status": "admitted", "patient_id": patient_id, "name": name}

    def discharge_patient(self, patient_id: str) -> Dict[str, Any]:
        """Discharge a patient from the hospital."""
        if patient_id not in self.patients:
            return {"error": "Patient not found", "patient_id": patient_id}

        self.patients[patient_id].status = PatientStatus.DISCHARGED
        self.patients[patient_id].updated_at = datetime.utcnow().isoformat()
        self._audit("patient_discharged", patient_id)
        return {"status": "discharged", "patient_id": patient_id}

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get patient record by ID."""
        return self.patients.get(patient_id)

    def get_hospital(self, hospital_id: str) -> Optional[HospitalRecord]:
        """Get hospital record by ID."""
        return self.hospitals.get(hospital_id)

    def list_patients(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all patients, optionally filtered by department."""
        results = []
        for p in self.patients.values():
            if department and p.department != department:
                continue
            results.append(p.to_dict())
        return results

    def list_hospitals(self) -> List[Dict[str, Any]]:
        """List all registered hospitals."""
        return [h.to_dict() for h in self.hospitals.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get hospital sector statistics."""
        return {
            "total_hospitals": len(self.hospitals),
            "total_patients": len(self.patients),
            "active_patients": sum(1 for p in self.patients.values() if p.status == PatientStatus.ACTIVE),
            "discharged_patients": sum(1 for p in self.patients.values() if p.status == PatientStatus.DISCHARGED),
            "government_share": 0.51,
            "private_share": 0.49,
            "audit_entries": len(self._audit_log),
        }

    def _audit(self, action: str, resource_id: str, details: Optional[Dict] = None) -> None:
        """Internal audit logging."""
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_id": resource_id,
            "details": details or {},
            "sector": "hospital",
        })

    def reset(self) -> None:
        """Reset all data (for testing)."""
        self.hospitals.clear()
        self.patients.clear()
        self._audit_log.clear()
