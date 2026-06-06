"""
Data Lake: Hash Chain
=====================
Tamper-evident hash chain for Data Lake records.

Each record is linked to the previous record via its hash,
creating an immutable chain that can be verified at any time.

Features:
- SHA-256 based hash chain
- Genesis block creation
- Tamper detection
- Chain verification
- Export/import
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DataLake.HashChain")


@dataclass
class ChainBlock:
    """A single block in the hash chain."""
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    block_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.block_hash:
            self.block_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute the hash of this block."""
        content = f"{self.index}{self.timestamp}{self.data_hash}{self.previous_hash}{json.dumps(self.metadata, sort_keys=True)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainBlock":
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            data_hash=data["data_hash"],
            previous_hash=data["previous_hash"],
            block_hash=data.get("block_hash", ""),
            metadata=data.get("metadata", {}),
        )


class HashChain:
    """
    Tamper-evident hash chain for Data Lake records.
    
    Usage:
        chain = HashChain()
        
        # Add a record
        block = chain.add_record(record_data, metadata={"source": "gazette"})
        
        # Verify integrity
        if chain.verify():
            print("Chain is intact")
        else:
            print("Tampering detected!")
    """
    
    def __init__(self, storage_path: str = "data/data_lake_hash_chain.json"):
        self.storage_path = storage_path
        self.chain: List[ChainBlock] = []
        self._load()
    
    def _load(self):
        """Load the chain from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chain = [ChainBlock.from_dict(block) for block in data]
                logger.info(f"Loaded hash chain with {len(self.chain)} blocks")
            except Exception as e:
                logger.warning(f"Failed to load hash chain: {e}")
                self._create_genesis()
        else:
            self._create_genesis()
    
    def _save(self):
        """Save the chain to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([block.to_dict() for block in self.chain], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save hash chain: {e}")
    
    def _create_genesis(self):
        """Create the genesis block."""
        genesis = ChainBlock(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            data_hash=hashlib.sha256(b"AsimNexus Data Lake Genesis Block").hexdigest(),
            previous_hash="0" * 64,
            metadata={"description": "Data Lake Genesis Block", "version": "1.0"},
        )
        self.chain = [genesis]
        self._save()
        logger.info("Created genesis block for Data Lake hash chain")
    
    def add_record(self, data: Any, metadata: Dict[str, Any] = None) -> ChainBlock:
        """
        Add a record to the hash chain.
        
        Args:
            data: The data to hash (will be JSON-serialized)
            metadata: Optional metadata about the record
            
        Returns:
            The new ChainBlock
        """
        # Compute data hash
        data_str = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        
        previous_hash = self.chain[-1].block_hash if self.chain else "0" * 64
        
        block = ChainBlock(
            index=len(self.chain),
            timestamp=datetime.utcnow().isoformat(),
            data_hash=data_hash,
            previous_hash=previous_hash,
            metadata=metadata or {},
        )
        
        self.chain.append(block)
        self._save()
        
        return block
    
    def verify(self) -> bool:
        """
        Verify the integrity of the entire chain.
        
        Returns:
            True if the chain is intact, False if tampering is detected
        """
        if not self.chain:
            return True
        
        # Verify genesis block
        genesis = self.chain[0]
        if genesis.index != 0:
            logger.error("Genesis block index is not 0")
            return False
        if genesis.previous_hash != "0" * 64:
            logger.error("Genesis block previous_hash is not zero")
            return False
        
        # Verify each block
        for i, block in enumerate(self.chain):
            # Recompute and verify block hash
            expected_hash = block._compute_hash()
            if block.block_hash != expected_hash:
                logger.error(f"Block {i} hash mismatch: expected {expected_hash}, got {block.block_hash}")
                return False
            
            # Verify chain linkage
            if i > 0:
                if block.previous_hash != self.chain[i - 1].block_hash:
                    logger.error(f"Block {i} previous_hash mismatch")
                    return False
        
        return True
    
    def detect_tampering(self) -> List[Dict[str, Any]]:
        """
        Detect tampering and return details about tampered blocks.
        
        Returns:
            List of tampered block details
        """
        tampered = []
        
        for i, block in enumerate(self.chain):
            expected_hash = block._compute_hash()
            if block.block_hash != expected_hash:
                tampered.append({
                    "index": i,
                    "expected_hash": expected_hash,
                    "stored_hash": block.block_hash,
                    "timestamp": block.timestamp,
                    "reason": "Block hash mismatch",
                })
            
            if i > 0 and block.previous_hash != self.chain[i - 1].block_hash:
                tampered.append({
                    "index": i,
                    "expected_previous": self.chain[i - 1].block_hash,
                    "stored_previous": block.previous_hash,
                    "timestamp": block.timestamp,
                    "reason": "Chain linkage broken",
                })
        
        return tampered
    
    def get_block(self, index: int) -> Optional[ChainBlock]:
        """Get a block by index."""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_latest_block(self) -> Optional[ChainBlock]:
        """Get the most recent block."""
        return self.chain[-1] if self.chain else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics."""
        return {
            "chain_length": len(self.chain),
            "integrity_verified": self.verify(),
            "genesis_timestamp": self.chain[0].timestamp if self.chain else None,
            "latest_timestamp": self.chain[-1].timestamp if self.chain else None,
            "tampered_blocks": len(self.detect_tampering()),
        }


# Singleton
hash_chain = HashChain()
