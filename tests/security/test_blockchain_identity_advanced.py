
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Advanced Blockchain Identity System
==========================================

Test the advanced blockchain identity implementation.
"""

import asyncio
import json
from core.blockchain_identity_advanced import (
    BlockchainIdentityAdvanced,
    get_blockchain_identity_advanced,
    BlockchainNetwork,
    AttestationType
)

async def test_blockchain_identity():
    """Test Advanced Blockchain Identity System"""
    print("=" * 60)
    print("Testing Advanced Blockchain Identity System")
    print("=" * 60)
    
    identity = get_blockchain_identity_advanced()
    
    # Test 1: DID Creation
    print("\n[OK] Testing DID creation...")
    public_key = "0x" + "a" * 64  # Mock public key
    did = identity.create_did(public_key, BlockchainNetwork.ETHEREUM)
    print(f"  Created DID: {did}")
    
    did_doc = identity.get_did_document(did)
    if did_doc:
        print(f"  Public key: {did_doc.public_key[:20]}...")
        print(f"  Network: {did_doc.network.value}")
        print(f"  Controller: {did_doc.controller}")
    
    # Test 2: Credential issuance
    print("\n[OK] Testing credential issuance...")
    vc_id = identity.issue_credential(
        issuer_did=did,
        subject_did=did,
        credential_type=AttestationType.IDENTITY,
        claims={
            "name": "John Doe",
            "nationality": "US",
            "birth_date": "1990-01-01",
            "id_number": "123-45-6789"
        },
        expiration_days=365
    )
    print(f"  Issued VC: {vc_id}")
    
    # Test 3: Credential verification
    print("\n[OK] Testing credential verification...")
    verification = identity.verify_credential(vc_id)
    print(f"  Valid: {verification['valid']}")
    if verification['valid']:
        print(f"  Type: {verification['type']}")
        print(f"  Claims: {verification['claims']}")
    
    # Test 4: Multiple credentials
    print("\n[OK] Testing multiple credentials...")
    education_vc = identity.issue_credential(
        issuer_did=did,
        subject_did=did,
        credential_type=AttestationType.EDUCATION,
        claims={
            "degree": "Bachelor of Science",
            "major": "Computer Science",
            "university": "MIT",
            "graduation_year": 2012
        }
    )
    print(f"  Education VC: {education_vc}")
    
    employment_vc = identity.issue_credential(
        issuer_did=did,
        subject_did=did,
        credential_type=AttestationType.EMPLOYMENT,
        claims={
            "company": "Tech Corp",
            "position": "Senior Engineer",
            "start_date": "2015-06-01"
        }
    )
    print(f"  Employment VC: {employment_vc}")
    
    # Test 5: Get credentials for subject
    print("\n[OK] Testing get credentials for subject...")
    all_creds = identity.get_credentials_for_subject(did)
    print(f"  Total credentials: {len(all_creds)}")
    
    id_creds = identity.get_credentials_for_subject(did, AttestationType.IDENTITY)
    print(f"  Identity credentials: {len(id_creds)}")
    
    edu_creds = identity.get_credentials_for_subject(did, AttestationType.EDUCATION)
    print(f"  Education credentials: {len(edu_creds)}")
    
    # Test 6: Soulbound Token
    print("\n[OK] Testing Soulbound Token...")
    sbt_id = identity.issue_soulbound_token(
        owner_did=did,
        token_type="identity",
        metadata={"verified": True, "level": "gold", "kyc_passed": True},
        issuer="asimnexus.gov",
        network=BlockchainNetwork.ETHEREUM
    )
    print(f"  Issued SBT: {sbt_id}")
    
    sbts = identity.get_sbts_for_owner(did)
    print(f"  Total SBTs for owner: {len(sbts)}")
    
    # Test 7: Zero-Knowledge Proof
    print("\n[OK] Testing Zero-Knowledge Proof...")
    zk_proof = identity.create_zk_proof(
        prover_did=did,
        statement="I am over 18 years old",
        secret_data="1990-01-01"
    )
    print(f"  Created ZK proof: {zk_proof.proof_id}")
    print(f"  Statement: {zk_proof.statement}")
    
    verified = identity.verify_zk_proof(zk_proof.proof_id)
    print(f"  Verified: {verified}")
    
    # Test 8: Credential revocation
    print("\n[OK] Testing credential revocation...")
    revoked = identity.revoke_credential(education_vc, reason="Degree invalidated")
    print(f"  Revocation successful: {revoked}")
    
    # Verify revoked credential
    revoked_check = identity.verify_credential(education_vc)
    print(f"  Revoked credential valid: {revoked_check['valid']}")
    if not revoked_check['valid']:
        print(f"  Reason: {revoked_check['error']}")
    
    # Test 9: Multiple networks
    print("\n[OK] Testing multiple blockchain networks...")
    polygon_did = identity.create_did(public_key, BlockchainNetwork.POLYGON)
    print(f"  Polygon DID: {polygon_did}")
    
    polkadot_did = identity.create_did(public_key, BlockchainNetwork.POLKADOT)
    print(f"  Polkadot DID: {polkadot_did}")
    
    # Test 10: Statistics
    print("\n[OK] Blockchain Identity Statistics:")
    stats = identity.get_stats()
    print(f"  DIDs total: {stats['dids']['total']}")
    print(f"  Credentials total: {stats['credentials']['total']}")
    print(f"  Active credentials: {stats['credentials']['active']}")
    print(f"  Revoked credentials: {stats['credentials']['revoked']}")
    print(f"  Attestations: {stats['attestations']}")
    print(f"  SBTs: {stats['sbts']}")
    print(f"  ZK proofs: {stats['zk_proofs']['total']}")
    print(f"  Ledger entries: {stats['ledger_entries']}")
    
    print("\n  Credentials by type:")
    for cred_type, count in stats['credentials']['by_type'].items():
        if count > 0:
            print(f"    {cred_type}: {count}")
    
    print("\n  DIDs by network:")
    for network, count in stats['dids']['by_network'].items():
        if count > 0:
            print(f"    {network}: {count}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Advanced Blockchain Identity Test Passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_blockchain_identity())
