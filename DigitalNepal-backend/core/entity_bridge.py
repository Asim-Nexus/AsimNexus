#!/usr/bin/env python3
"""AsimNexus - Master Entity Connector
Connects all 57,000+ entities systematically
"""

from typing import Dict, Any, Optional
from enum import Enum

class EntityType(Enum):
    GOVERNMENT = "government"
    COMPANY = "company"
    EDUCATION = "education"
    HEALTH = "health"
    CULTURE = "culture"

class Sector(Enum):
    # Government (51% threshold)
    PM_OFFICE = "pm_office"
    FINANCE = "finance"
    HOME = "home"
    HEALTH = "health"
    
    # Company (49% threshold)
    BANKING = "banking"
    TELECOM = "telecom"
    ENERGY = "energy"
    
    # Education
    UNIVERSITY = "university"
    SCHOOL = "school"
    
    # Health
    HOSPITAL = "hospital"
    
    # Culture
    LANGUAGE = "language"
    ETHNICITY = "ethnicity"

class AsimNexusBridge:
    """
    Master Connector - connects all entities
    - Their System remains unchanged
    - We connect via API/Router/Adapter
    - All data flows through unified interface
    """
    
    def __init__(self):
        self.entities = {}
        self._load_entities()
    
    def _load_entities(self):
        """Load all entities from registry"""
        from connectors.nepal_connectors import (
            MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS
        )
        self.entities = {
            "ministry": MINISTRIES,
            "province": PROVINCES,
            "district": DISTRICTS,
            "bank": BANKS,
            "isp": ISPS,
        }
    
    async def connect_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Connect to any entity via bridge"""
        registry = self.entities.get(entity_type)
        if not registry:
            return {"error": f"Entity type {entity_type} not found"}
        
        entity = registry.get(entity_id)
        if not entity:
            return {"error": f"Entity {entity_id} not found in {entity_type}"}
        
        return {
            "status": "connected",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity": entity,
            "integration": "bridge_mode"
        }
    
    async def get_all_entities(self, entity_type: str) -> Dict[str, Any]:
        """Get all entities of a type"""
        registry = self.entities.get(entity_type, {})
        return {
            "count": len(registry),
            "entities": list(registry.values()),
            "sector": "government" if entity_type in ["ministry", "province", "district"] else "company"
        }

# Singleton instance
_bridge = None

def get_bridge() -> AsimNexusBridge:
    global _bridge
    if _bridge is None:
        _bridge = AsimNexusBridge()
    return _bridge

__all__ = ["EntityType", "Sector", "AsimNexusBridge", "get_bridge"]