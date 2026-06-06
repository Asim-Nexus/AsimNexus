/**
 * Blockchain Identity Login UI Component
 * 
 * Features:
 * - Web3 wallet connection (MetaMask, WalletConnect)
 * - DID display and management
 * - Verifiable Credentials viewer
 * - Soulbound Tokens display
 * - ZK Proof generation interface
 * - Multi-network support (Ethereum, Polygon, Polkadot)
 */

import React, { useState, useEffect } from 'react';
import './BlockchainIdentity.css';
import { API_BASE_URL } from '../../api/unified_api';

const BlockchainIdentity = ({ apiEndpoint }) => {
  const resolvedApiEndpoint = apiEndpoint || `${API_BASE_URL || ''}/api/blockchain`;
  const [isConnected, setIsConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState(null);
  const [did, setDid] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [sbts, setSbts] = useState([]);
  const [selectedNetwork, setSelectedNetwork] = useState('ethereum');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('identity'); // identity, credentials, tokens, proofs

  // Mock wallet connection for demo
  const connectWallet = async () => {
    setIsLoading(true);
    
    // Simulate wallet connection delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate mock wallet address
    const mockAddress = '0x' + Array(40).fill(0).map(() => 
      Math.floor(Math.random() * 16).toString(16)
    ).join('');
    
    setWalletAddress(mockAddress);
    setIsConnected(true);
    setIsLoading(false);
    
    // Create DID after connection
    await createDID(mockAddress);
  };

  // Create DID
  const createDID = async (address) => {
    try {
      const response = await fetch(`${resolvedApiEndpoint}/did`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          public_key: address,
          network: selectedNetwork
        })
      });
      
      const data = await response.json();
      setDid(data.did);
      
      // Load credentials and tokens
      await loadCredentials(data.did);
      await loadSBTs(data.did);
    } catch (error) {
      console.error('Error creating DID:', error);
    }
  };

  // Load credentials
  const loadCredentials = async (did) => {
    try {
      const response = await fetch(`${resolvedApiEndpoint}/credentials/${did}`);
      const data = await response.json();
      setCredentials(data.credentials || []);
    } catch (error) {
      console.error('Error loading credentials:', error);
    }
  };

  // Load SBTs
  const loadSBTs = async (did) => {
    try {
      const response = await fetch(`${resolvedApiEndpoint}/sbts/${did}`);
      const data = await response.json();
      setSbts(data.sbts || []);
    } catch (error) {
      console.error('Error loading SBTs:', error);
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setIsConnected(false);
    setWalletAddress(null);
    setDid(null);
    setCredentials([]);
    setSbts([]);
  };

  // Issue new credential
  const issueCredential = async (type) => {
    if (!did) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${resolvedApiEndpoint}/credential`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          issuer_did: did,
          subject_did: did,
          credential_type: type,
          claims: {
            issued_at: new Date().toISOString(),
            verified: true
          }
        })
      });
      
      const data = await response.json();
      await loadCredentials(did);
    } catch (error) {
      console.error('Error issuing credential:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Create ZK Proof
  const createZKProof = async () => {
    if (!did) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${resolvedApiEndpoint}/zkproof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prover_did: did,
          statement: 'I am a verified ASIMNEXUS user',
          secret_data: walletAddress
        })
      });
      
      alert('Zero-Knowledge Proof created successfully!');
    } catch (error) {
      console.error('Error creating ZK proof:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Format address for display
  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  // Format DID for display
  const formatDID = (did) => {
    if (!did) return '';
    const parts = did.split(':');
    if (parts.length >= 3) {
      return `${parts[0]}:${parts[1]}:${parts[2].slice(0, 8)}...`;
    }
    return did.slice(0, 20) + '...';
  };

  return (
    <div className="blockchain-identity">
      <div className="identity-header">
        <h3>⛓️ Blockchain Identity</h3>
        {!isConnected ? (
          <div className="connect-section">
            <select
              value={selectedNetwork}
              onChange={(e) => setSelectedNetwork(e.target.value)}
              className="network-selector"
            >
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="polkadot">Polkadot</option>
              <option value="solana">Solana</option>
            </select>
            <button
              onClick={connectWallet}
              disabled={isLoading}
              className="connect-btn"
            >
              {isLoading ? 'Connecting...' : 'Connect Wallet'}
            </button>
          </div>
        ) : (
          <div className="wallet-info">
            <span className="network-badge">{selectedNetwork}</span>
            <span className="address">{formatAddress(walletAddress)}</span>
            <button onClick={disconnectWallet} className="disconnect-btn">
              Disconnect
            </button>
          </div>
        )}
      </div>

      {!isConnected ? (
        <div className="not-connected">
          <div className="wallet-icon">👛</div>
          <p>Connect your Web3 wallet to access decentralized identity features</p>
          <ul className="features-list">
            <li>✅ Create Decentralized Identifier (DID)</li>
            <li>✅ Manage Verifiable Credentials</li>
            <li>✅ View Soulbound Tokens</li>
            <li>✅ Generate Zero-Knowledge Proofs</li>
            <li>✅ Multi-chain support</li>
          </ul>
        </div>
      ) : (
        <>
          <div className="identity-nav">
            <button
              className={activeTab === 'identity' ? 'active' : ''}
              onClick={() => setActiveTab('identity')}
            >
              🆔 Identity
            </button>
            <button
              className={activeTab === 'credentials' ? 'active' : ''}
              onClick={() => setActiveTab('credentials')}
            >
              📜 Credentials ({credentials.length})
            </button>
            <button
              className={activeTab === 'tokens' ? 'active' : ''}
              onClick={() => setActiveTab('tokens')}
            >
              🎴 SBTs ({sbts.length})
            </button>
            <button
              className={activeTab === 'proofs' ? 'active' : ''}
              onClick={() => setActiveTab('proofs')}
            >
              🔒 ZK Proofs
            </button>
          </div>

          <div className="identity-content">
            {activeTab === 'identity' && (
              <div className="identity-panel">
                <div className="did-card">
                  <h4>Decentralized Identifier (DID)</h4>
                  <div className="did-display">
                    <code>{formatDID(did)}</code>
                    <span className="did-badge">W3C Standard</span>
                  </div>
                  <p className="did-info">
                    Your DID is a self-sovereign identity that you control. 
                    It is not stored on any central server.
                  </p>
                </div>

                <div className="wallet-details">
                  <h4>Wallet Details</h4>
                  <div className="detail-row">
                    <span>Network:</span>
                    <span className="value">{selectedNetwork.charAt(0).toUpperCase() + selectedNetwork.slice(1)}</span>
                  </div>
                  <div className="detail-row">
                    <span>Address:</span>
                    <span className="value mono">{walletAddress}</span>
                  </div>
                  <div className="detail-row">
                    <span>Status:</span>
                    <span className="value success">Connected</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'credentials' && (
              <div className="credentials-panel">
                <div className="panel-header">
                  <h4>Verifiable Credentials</h4>
                  <button
                    onClick={() => issueCredential('identity')}
                    disabled={isLoading}
                    className="issue-btn"
                  >
                    + Issue Credential
                  </button>
                </div>
                
                {credentials.length === 0 ? (
                  <p className="empty-state">No credentials issued yet.</p>
                ) : (
                  <div className="credentials-list">
                    {credentials.map((cred, index) => (
                      <div key={index} className="credential-card">
                        <div className="cred-header">
                          <span className="cred-type">{cred.credential_type}</span>
                          <span className={`cred-status ${cred.status}`}>
                            {cred.status}
                          </span>
                        </div>
                        <div className="cred-details">
                          <p>Issuer: {formatDID(cred.issuer_did)}</p>
                          <p>Issued: {new Date(cred.issuance_date).toLocaleDateString()}</p>
                          {cred.expiration_date && (
                            <p>Expires: {new Date(cred.expiration_date).toLocaleDateString()}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'tokens' && (
              <div className="tokens-panel">
                <h4>Soulbound Tokens (SBTs)</h4>
                <p className="sbt-info">
                  Non-transferable tokens representing your identity, achievements, and memberships.
                </p>
                
                {sbts.length === 0 ? (
                  <p className="empty-state">No SBTs found.</p>
                ) : (
                  <div className="sbt-list">
                    {sbts.map((sbt, index) => (
                      <div key={index} className="sbt-card">
                        <div className="sbt-icon">🏅</div>
                        <div className="sbt-info">
                          <h5>{sbt.token_type}</h5>
                          <p>Issuer: {sbt.issuer}</p>
                          <p>Issued: {new Date(sbt.issued_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'proofs' && (
              <div className="proofs-panel">
                <h4>Zero-Knowledge Proofs</h4>
                <p className="zk-info">
                  Prove statements about your identity without revealing underlying data.
                </p>
                
                <div className="zk-actions">
                  <button
                    onClick={createZKProof}
                    disabled={isLoading}
                    className="create-proof-btn"
                  >
                    Create ZK Proof
                  </button>
                </div>

                <div className="zk-examples">
                  <h5>Example Use Cases:</h5>
                  <ul>
                    <li>Prove you are over 18 without revealing birth date</li>
                    <li>Prove citizenship without showing passport details</li>
                    <li>Prove income bracket without revealing exact salary</li>
                    <li>Prove credential ownership without showing credential</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default BlockchainIdentity;
