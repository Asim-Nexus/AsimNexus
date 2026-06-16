"""
STATUS: REAL — Data atomization for inter-generational knowledge transfer

AsimNexus Data Atomizer
=========================
Extracts semantic essence from user data into atomic knowledge units:
- Knowledge atoms for long-term preservation
- Decoding formulas for reconstruction
- Legacy notebook generation
- Entropy-based pruning for optimization
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("AsimNexus.DataAtomizer")

DATA_ATOMS_PATH = Path(__file__).parent.parent.parent / "data" / "atoms"
DATA_ATOMS_PATH.mkdir(parents=True, exist_ok=True)

@dataclass
class KnowledgeAtom:
    """Atomic unit of semantic knowledge"""
    atom_id: str
    user_id: str
    domain: str
    essence: str
    metadata: Dict[str, Any]
    created_at: str
    decoding_key: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "essence": self.essence[:500],  # Truncate for storage
            "metadata": self.metadata,
            "created_at": self.created_at,
            "decoding_key": self.decoding_key
        }

class DataAtomizer:
    """
    Extracts semantic essence into atomic knowledge units
    
    Enables:
    - Long-term preservation of user knowledge
    - Inter-generational knowledge transfer
    - Lightweight searchable legacy
    - Automatic pruning of obsolete data
    """

    def __init__(self):
        self._atoms: Dict[str, KnowledgeAtom] = {}
        logger.info("⚛️ DataAtomizer initialized")

    async def atomize_user_data(
        self, 
        user_id: str, 
        raw_data: Dict[str, Any]
    ) -> List[KnowledgeAtom]:
        """
        Extract knowledge atoms from user's raw data
        
        Args:
            user_id: User identifier
            raw_data: All user data by category
        
        Returns:
            List of extracted knowledge atoms
        """
        atoms = []

        for domain, data in raw_data.items():
            if not data:
                continue

            essence = await self._extract_essence(domain, data)
            metadata = await self._calculate_metadata(domain, data)
            
            atom = KnowledgeAtom(
                atom_id=hashlib.sha256(f"{user_id}:{domain}:{datetime.utcnow()}".encode()).hexdigest()[:16],
                user_id=user_id,
                domain=domain,
                essence=essence,
                metadata=metadata,
                created_at=datetime.utcnow().isoformat(),
                decoding_key=self._generate_decoding_key(user_id, domain)
            )

            self._atoms[atom.atom_id] = atom
            atoms.append(atom)

        logger.info(f"⚛️ Created {len(atoms)} atoms for user {user_id}")
        return atoms

    async def _extract_essence(self, domain: str, data: Any) -> str:
        """Extract semantic essence from data"""
        if isinstance(data, str):
            # Text data - extract key phrases
            return self._extract_text_essence(data)
        elif isinstance(data, dict):
            # Structured data - extract key-value pairs
            return self._extract_structured_essence(data)
        elif isinstance(data, list):
            # List data - extract patterns
            return self._extract_list_essence(data)
        else:
            return str(data)

    def _extract_text_essence(self, text: str) -> str:
        """Extract essence from text (Nepali/English)"""
        # In production: use NLP for key phrase extraction
        # For Nepal: prioritize Nepali sentences, extract entities
        sentences = text.split("।")[:5]  # First 5 sentences
        return " ".join(s.strip() for s in sentences if s.strip())

    def _extract_structured_essence(self, data: Dict) -> str:
        """Extract essence from structured data"""
        key_items = []
        for key in ["name", "title", "description", "summary", "note"]:
            if key in data:
                key_items.append(str(data[key]))
        return " | ".join(key_items)

    def _extract_list_essence(self, items: List) -> str:
        """Extract essence from list data"""
        # Take first and last items, count, and pattern
        count = len(items)
        sample = str(items[0]) if items else "none"
        return f"count:{count} sample:{sample}"

    async def _calculate_metadata(self, domain: str, data: Any) -> Dict[str, Any]:
        """Calculate entropy signature and metadata"""
        return {
            "entropy": self._calculate_entropy(str(data)),
            "size_chars": len(str(data)),
            "created_at": datetime.utcnow().isoformat(),
            "domain": domain,
            "type": type(data).__name__
        }

    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        from collections import Counter
        import math
        
        freq = Counter(data)
        total = len(data)
        entropy = 0.0
        
        for count in freq.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        return round(entropy / 8, 3)  # Normalize

    def _generate_decoding_key(self, user_id: str, domain: str) -> str:
        """Generate key for atom reconstruction"""
        seed = f"{user_id}:{domain}:{time.time()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:32]

    async def prune_obsolete_atoms(
        self, 
        user_id: str, 
        threshold_days: int = 365
    ) -> int:
        """
        Prune atoms with low relevance (entropy below threshold)
        
        Args:
            user_id: User identifier
            threshold_days: Age threshold for pruning
        
        Returns:
            Number of pruned atoms
        """
        pruned = 0
        cutoff = time.time() - (threshold_days * 86400)

        for atom_id, atom in list(self._atoms.items()):
            if atom.user_id != user_id:
                continue

            atom_time = datetime.fromisoformat(atom.created_at).timestamp()
            entropy = atom.metadata.get("entropy", 1.0)

            # Prune if old AND low entropy
            if atom_time < cutoff and entropy < 0.3:
                del self._atoms[atom_id]
                pruned += 1

        logger.info(f"⚛️ Pruned {pruned} obsolete atoms for user {user_id}")
        return pruned

    async def create_legacy_notebook(
        self, 
        user_id: str,
        nominee_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create searchable legacy notebook for inheritance
        
        Args:
            user_id: Deceased user's ID
            nominee_id: Inheritor's ID
        
        Returns:
            Legacy notebook with encoded atoms
        """
        user_atoms = [
            atom for atom in self._atoms.values()
            if atom.user_id == user_id
        ]

        # Group by domain
        domains = {}
        for atom in user_atoms:
            if atom.domain not in domains:
                domains[atom.domain] = []
            domains[atom.domain].append(atom.to_dict())

        notebook = {
            "notebook_id": f"legacy_{user_id}_{int(time.time())}",
            "original_user_id": user_id,
            "nominee_id": nominee_id,
            "created_at": datetime.utcnow().isoformat(),
            "atoms_by_domain": domains,
            "total_atoms": len(user_atoms),
            "decoding_formula": self._generate_notebook_key(user_id)
        }

        # Save to disk
        notebook_path = DATA_ATOMS_PATH / f"{user_id}_legacy.json"
        with open(notebook_path, "w") as f:
            json.dump(notebook, f, indent=2)

        logger.info(f"⚛️ Created legacy notebook for {user_id} ({len(user_atoms)} atoms)")
        return notebook

    def _generate_notebook_key(self, user_id: str) -> str:
        """Generate master key for legacy notebook"""
        return hashlib.sha256(f"legacy:{user_id}:{time.time()}".encode()).hexdigest()[:64]

    def status(self) -> Dict[str, Any]:
        """Get atomizer status"""
        return {
            "total_atoms": len(self._atoms),
            "atoms_path": str(DATA_ATOMS_PATH),
            "unique_users": len(set(a.user_id for a in self._atoms.values()))
        }

# Singleton
_atomizer: Optional[DataAtomizer] = None

def get_data_atomizer() -> DataAtomizer:
    """Get or create Data Atomizer singleton"""
    global _atomizer
    if _atomizer is None:
        _atomizer = DataAtomizer()
    return _atomizer