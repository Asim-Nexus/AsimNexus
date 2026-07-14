"""
Data Atomizer
=============
Atomizes user data into granular, privacy-preserving atoms
for fine-grained access control and data sovereignty.
"""

import json
import hashlib
import logging
import threading
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_instance = None
_instance_lock = threading.Lock()


@dataclass
class DataAtom:
    """A single atom of user data."""
    atom_id: str
    user_id: str
    category: str
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    access_count: int = 0


class DataAtomizer:
    """Atomizes user data into granular atoms."""

    def __init__(self):
        self._atoms: Dict[str, DataAtom] = {}
        self._lock = threading.Lock()

    async def atomize_user_data(
        self,
        user_id: str,
        data: Dict[str, Any],
        prefix: str = "",
    ) -> List[DataAtom]:
        """Atomize user data into individual atoms."""
        atoms = []

        def _flatten(obj: Any, path: str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    _flatten(value, new_path)
            else:
                atom_id = hashlib.md5(f"{user_id}:{path}".encode()).hexdigest()[:16]
                atoms.append(DataAtom(
                    atom_id=atom_id,
                    user_id=user_id,
                    category=path.split(".")[0] if "." in path else path,
                    key=path,
                    value=obj,
                ))

        _flatten(data, prefix)

        with self._lock:
            for atom in atoms:
                self._atoms[atom.atom_id] = atom

        logger.info(f"Atomized {len(atoms)} atoms for user {user_id}")
        return atoms

    def get_atom(self, atom_id: str) -> Optional[DataAtom]:
        """Get an atom by ID."""
        with self._lock:
            atom = self._atoms.get(atom_id)
            if atom:
                atom.access_count += 1
            return atom

    def get_user_atoms(self, user_id: str) -> List[DataAtom]:
        """Get all atoms for a user."""
        with self._lock:
            return [a for a in self._atoms.values() if a.user_id == user_id]

    def status(self) -> dict:
        """Get data atomizer status."""
        with self._lock:
            return {
                "total_atoms": len(self._atoms),
                "available": True,
            }


def get_data_atomizer() -> DataAtomizer:
    """Get or create the singleton DataAtomizer instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = DataAtomizer()
    return _instance


def reset_data_atomizer() -> None:
    """Reset the singleton for testing."""
    global _instance
    with _instance_lock:
        _instance = None
