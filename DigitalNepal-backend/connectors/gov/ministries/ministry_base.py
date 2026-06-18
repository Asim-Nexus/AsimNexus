#!/usr/bin/env python3
"""AsimNexus — Ministry Base Connector"""

class MinistryConnector:
    def __init__(self, name: str, sector: str, balance: str = "51%"):
        self.name = name
        self.sector = sector
        self.balance = balance
        self.api_prefix = f"/api/v1/gov/{sector}"
        self.active = True
    
    async def get_status(self):
        return {"name": self.name, "sector": self.sector, "balance": self.balance, "active": self.active}