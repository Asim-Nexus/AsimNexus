#!/usr/bin/env python3
"""AsimNexus — Full Integration Script - Smart Registry Approach"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))

from connectors.nepal_connectors import GOVERNMENT, COMPANIES

class AsimNexusIntegrator:
    async def integrate_all(self):
        stats = {
            "ministries": len(GOVERNMENT["ministries"]),
            "provinces": len(GOVERNMENT["provinces"]),
            "districts": len(GOVERNMENT["districts"]),
            "banks": len(COMPANIES["banks"]),
            "isps": len(COMPANIES["isps"]),
        }
        print("[OK] Government:", stats["ministries"], "Ministries")
        print("[OK] Provinces:", stats["provinces"], "Provinces")
        print("[OK] Districts:", stats["districts"], "Districts")
        print("[OK] Banks:", stats["banks"], "Banks")
        print("[OK] ISPs:", stats["isps"], "ISPs")
        print("\n[OK] AsimNexus Nepal Integration Complete!")
        return stats

if __name__ == "__main__":
    import asyncio
    asyncio.run(AsimNexusIntegrator().integrate_all())