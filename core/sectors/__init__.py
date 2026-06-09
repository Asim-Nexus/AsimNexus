"""
ASIMNEXUS Sector Modules
=======================
Specialized sector modules for the 51/49 constitutional balance:

- Hospital: Healthcare sector management & compliance
- Hotel: Hospitality sector management
- Education: Educational institution management
- Banking: Financial sector management

Each sector enforces the Dharma-Chakra constitutional balance:
51% Government / 49% Private / 100% Personal OS capability.
"""

from .hospital_sector import HospitalSector, HospitalRecord, PatientRecord
from .hotel_sector import HotelSector, HotelBooking, RoomRecord
from .education_sector import EducationSector, CourseRecord, StudentRecord
from .banking_sector import BankingSector, AccountRecord, TransactionRecord

__all__ = [
    "HospitalSector", "HospitalRecord", "PatientRecord",
    "HotelSector", "HotelBooking", "RoomRecord",
    "EducationSector", "CourseRecord", "StudentRecord",
    "BankingSector", "AccountRecord", "TransactionRecord",
]

# Sector registry for dynamic discovery
SECTOR_REGISTRY = {
    "hospital": HospitalSector,
    "hotel": HotelSector,
    "education": EducationSector,
    "banking": BankingSector,
}
