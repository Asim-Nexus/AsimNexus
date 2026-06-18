// Digital Nepal Frontend API Client
// Connects to AsimNexus backend

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Chat API
export const sendMessage = async (message, sector = 'general') => {
  const resp = await fetch(`${API_BASE}/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, sector })
  });
  return resp.json();
};

// Governance API
export const proposeAction = async (sector, action, isPublic = true) => {
  const resp = await fetch(`${API_BASE}/gov/propose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sector, action, is_public: isPublic })
  });
  return resp.json();
};

// Mesh Sync API
export const syncOperation = async (crdtId, operation, key, value) => {
  const resp = await fetch(`${API_BASE}/mesh/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ crdt_id: crdtId, operation, key, value })
  });
  return resp.json();
};

export const getMeshStatus = async () => {
  const resp = await fetch(`${API_BASE}/mesh/status`);
  return resp.json();
};

// System Status
export const getSystemStatus = async () => {
  const resp = await fetch(`${API_BASE}/status`);
  return resp.json();
};

export default { sendMessage, proposeAction, syncOperation, getMeshStatus, getSystemStatus };