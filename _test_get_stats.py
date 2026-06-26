#!/usr/bin/env python3
"""
_test_get_stats.py - Test script for getting system statistics
AsimNexus System Stats
"""

import sys
sys.path.insert(0, '..')

def test_mirrror_stats():
    from core.mirror.mirror_module import get_mirror
    m = get_mirror('test')
    print(f"Mirror stats: {m.get_daily_report()}")

def test_consensus_stats():
    from core.consensus.clone_consensus_voting import CloneConsensusVoting
    c = CloneConsensusVoting()
    print(f"Consensus stats: {c.get_stats()}")

if __name__ == "__main__":
    test_mirrror_stats()
    test_consensus_stats()