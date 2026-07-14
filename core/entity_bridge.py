"""Entity bridge — connects different government/org entities in AsimNexus."""


class EntityBridge:
    """Bridges entities across different domains."""

    def __init__(self):
        self._connections = {}

    def connect_entity(self, entity_type: str, entity_id: str) -> dict:
        """Connect an entity by type and id."""
        key = f"{entity_type}:{entity_id}"
        self._connections[key] = {"type": entity_type, "id": entity_id}
        return {"status": "connected", "entity": key}

    def get_connections(self) -> dict:
        return self._connections


_bridge = EntityBridge()


def get_bridge() -> EntityBridge:
    """Return the singleton EntityBridge instance."""
    return _bridge
