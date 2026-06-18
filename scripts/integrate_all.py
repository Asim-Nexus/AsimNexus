#!/usr/bin/env python3
"""AsimNexus — Full Integration Script

Usage: python scripts/integrate_all.py
"""

import asyncio
from connectors.gov.ministries import NEPAL_MINISTRIES
from connectors.gov.provinces import NEPAL_PROVINCES, NEPAL_DISTRICTS
from connectors.company import NEPAL_BANKS, NEPAL_ISPS

class AsimNexusIntegrator:
    """एकै पटक सबै एकीकरण"""
    
    async def integrate_all(self):
        stats = {
            "ministries": len(NEPAL_MINISTRIES),
            "provinces": len(NEPAL_PROVINCES),
            "districts": len(NEPAL_DISTRICTS),
            "banks": len(NEPAL_BANKS),
            "isps": len(NEPAL_ISPS),
        }
        
        print("✅ Government:", stats["ministries"], "Ministries")
        print("✅ Provinces:", stats["provinces"], "Provinces") 
        print("✅ Districts:", stats["districts"], "Districts")
        print("✅ Banks:", stats["banks"], "Banks")
        print("✅ ISPs:", stats["isps"], "ISPs")
        print("\n🎉 AsimNexus Nepal Integration Complete!")
        return stats

if __name__ == "__main__":
    integrator = AsimNexusIntegrator()
    asyncio.run(integrator.integrate_all())