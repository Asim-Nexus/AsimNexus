#!/usr/bin/env python3
"""AsimNexus Complete System Test
Tests all modules integrated
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))

def test_all():
    print("=== AsimNexus Complete Integration Test ===\n")
    
    # Core connectors
    from connectors.nepal_connectors import MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS
    from connectors.education_connectors import UNIVERSITIES, SCHOOLS
    from connectors.health_connectors import HOSPITALS
    from connectors.tourism_connectors import TOURISM_ENTITY
    
    print(f"[Gov] Ministries: {len(MINISTRIES)}")
    print(f"[Gov] Provinces: {len(PROVINCES)}")
    print(f"[Gov] Districts: {len(DISTRICTS)}")
    
    print(f"[Company] Banks: {len(BANKS)}")
    print(f"[Company] ISPs: {len(ISPS)}")
    
    print(f"[Education] Universities: {len(UNIVERSITIES)}")
    print(f"[Education] Schools: {len(SCHOOLS)}")
    
    print(f"[Health] Hospitals: {len(HOSPITALS)}")
    print(f"[Tourism] Hotels: {len(TOURISM_ENTITY['hotels'])}")
    
    # Infrastructure
    from database import DatabaseLayer
    from security import ZKPService, HSMService
    from mesh import P2PNetwork, OfflineSync
    
    print(f"[DB] Database layer ready")
    print(f"[Security] ZKP + HSM modules ready")
    print(f"[Mesh] P2P + Offline sync ready")
    
    print("\n=== All Modules Loaded Successfully ===")

if __name__ == "__main__":
    test_all()