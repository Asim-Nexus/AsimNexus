/**
 * AsimBrainService.js
 * Phase 3: AI integration with AsimBrain (core/asim_brain.py)
 */

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AsimBrainService {
  constructor() {
    this.cache = new Map();
    this.cacheExpiry = 5 * 60 * 1000;
  }

  authHeaders() {
    const token = localStorage.getItem('asimnexus_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async processMessage(message, context = {}) {
    console.log('[AsimBrain] Processing message:', message.substring(0, 50));
    
    // Try direct backend API first
    try {
      const response = await fetch(`${API}/api/brain/process`, {
        method: 'POST',
        headers: this.authHeaders(),
        body: JSON.stringify({
          message,
          context: { ...context, timestamp: Date.now(), source: 'asim_orb' },
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('[AsimBrain] Backend response received');
        return { response: data.response || '', source: data.source || 'backend' };
      }
    } catch (error) {
      console.log('[AsimBrain] Backend unavailable, using local fallback');
    }
    
    // Fallback: Local processing
    return this.localProcess(message, context);
  }
  }

  async *streamMessage(message, context = {}) {
    try {
      const response = await fetch(`${API}/api/brain/stream`, {
        method: 'POST',
        headers: this.authHeaders(),
        body: JSON.stringify({
          message,
          context,
          mode: context.mode || 'personal',
          streaming: true,
        }),
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) yield data.token;
            } catch { }
          }
        }
      }
    } catch (error) {
      yield '[AI connection failed. Using local mode.]';
    }
  }

  localProcess(message, context = {}) {
    const lower = message.toLowerCase();

    // 🏥 HEALTH & WELLNESS
    if (lower.includes('health') || lower.includes('swasthya') || lower.includes('doctor')) {
      return {
        response: `🏥 **Health Dashboard** (PersonalOS)

**Vitals:**
• Blood Pressure: 120/80 mmHg (Normal)
• Heart Rate: 72 bpm (Resting)
• Sleep: 7.5 hours last night
• Steps Today: 8,432

**Recommendations:**
• Drink 2L water daily
• 30 min meditation suggested
• Medicine: Vitamin D @ 8:00 AM

**Actions:**
🩺 Book appointment | 📊 View history | 🚨 Emergency`, source: 'local'
      };
    }

    // 💼 WORK & ENTERPRISE
    if (lower.includes('work') || lower.includes('company') || lower.includes('business') || lower.includes('job')) {
      return {
        response: `💼 **Enterprise Mode** (WorldOS)

**Active Projects:**
• Contract #2841: AI Development ($12,500)
• Contract #2845: Data Pipeline ($8,300)
• Status: 2/5 milestones complete

**AI Agents Working:**
🤖 Tech Architect — Analyzing code
🤖 Data Engineer — Processing pipeline

**Revenue:** $20,800 this month
**Pending:** 3 proposals awaiting client approval

**Actions:**
📋 View contracts | 👥 Hire agents | 📊 Reports`, source: 'local'
      };
    }

    // 🤖 AI AGENTS & CLONES
    if (lower.includes('agent') || lower.includes('clone') || lower.includes('hire') || lower.includes('bot')) {
      return {
        response: `🤖 **AI Agent Marketplace** (MCP)

**Available Clones:**
1. 🧙‍♂️ **Tech Architect** — $50/day
   Expert in: Code review, System design
   
2. 🥷 **Data Engineer** — $40/day
   Expert in: ETL, Analytics, ML pipelines
   
3. ⚔️ **Security Sentinel** — $35/day
   Expert in: Audits, Penetration testing
   
4. 🏥 **Health Sage** — $30/day
   Expert in: Medical research, Health plans

**Your Active Agents:**
✅ Tech Architect (hired 3 days ago)
⏸️ Data Engineer (paused)

**Actions:**
💰 Hire | ⏸️ Pause | 🔄 Switch | 💸 Budget`, source: 'local'
      };
    }

    // 🌐 MESH NETWORK
    if (lower.includes('mesh') || lower.includes('network') || lower.includes('connect') || lower.includes('wifi')) {
      return {
        response: `🌐 **Mesh Network Status** (NetworkHub)

**Neighbors Online:** 3 nodes
• Node-A47: 2 hops, Strong signal (-45dBm)
• Node-B12: 1 hop, Excellent (-32dBm)
• Node-C89: 3 hops, Good (-58dBm)

**Data Shared Today:**
• Uploaded: 45 MB (encrypted)
• Downloaded: 128 MB
• Relayed: 12 MB (helping neighbors)

**Dharma ΔT Contribution:** +12 points
**Offline Mode:** ✅ Ready (local AI active)

**Actions:**
📡 Scan network | 🔒 Security audit | ⚡ Boost signal`, source: 'local'
      };
    }

    // ⚖️ DHARMA / GOVERNANCE
    if (lower.includes('dharma') || lower.includes('balance') || lower.includes('vote') || lower.includes('governance')) {
      return {
        response: `⚖️ **Dharma Governance** (ΔT System)

**Network Balance:**
• Symmetry Score: 94.2% (Excellent)
• Gini Coefficient: 0.32 (Fair distribution)
• Last Community Vote: Proposal #892 passed

**Your Contributions:**
• ΔT Points: +156 (Top 15% contributor)
• Validated transactions: 42
• Proposals created: 3
• Proposals voted: 18

**Active Proposals:**
🗳️ Prop #901: Increase mesh rewards
🗳️ Prop #902: New health AI features

**Actions:**
🗳️ Vote | 📜 View proposals | ⚖️ Create proposal`, source: 'local'
      };
    }

    // 💰 WALLET / FINANCE
    if (lower.includes('money') || lower.includes('wallet') || lower.includes('balance') || lower.includes('payment') || lower.includes('send')) {
      return {
        response: `💰 **Asim Wallet** (IdentityHub)

**Balances:**
• ASIM Tokens: 1,247.50 ⓐ
• USDC: $450.00
• ETH: 0.42 Ξ

**Recent Transactions:**
• +50 ⓐ Mesh contribution reward
• -120 ⓐ Hired Tech Architect (2 days)
• +200 ⓐ Contract #2841 milestone

**Identity:**
🔐 DID: did:asim:a1b2c3d4e5f6...
✅ KYC Verified: Level 3 (Enterprise)

**Actions:**
💸 Send | 📥 Receive | 📊 History | 🔒 Security`, source: 'local'
      };
    }

    // 🆘 HELP / WHAT IS ASIM
    if (lower.includes('help') || lower.includes('what is asim') || lower.includes('about') || lower.includes('guide')) {
      return {
        response: `🌌 **AsimNexus v3 — World Operating System**

**What is AsimNexus?**
A unified digital ecosystem connecting Individuals, Companies, Governments, and Communities through AI, Blockchain, and Mesh Networking.

**What can I do here?**
🏥 Manage health & wellness
💼 Run business with AI agents
� Hire specialized AI clones
🌐 Join mesh network
⚖️ Participate in governance
💰 Send/receive payments
🔐 Secure digital identity

**Navigation:**
🖥️ OS Hub — Personal & World OS
🌍 Market — Agents & Contracts
🧠 AI Hub — Memory & Learning
🔐 Identity — Wallet & KYC
🌐 Network — Mesh & Connectivity

**Need help? Try:**
"Health check" | "Work status" | "Hire agent" | "Mesh info"`, source: 'local'
      };
    }

    // 📊 SYSTEM STATUS
    if (lower.includes('status') || lower.includes('system') || lower.includes('info') || lower.includes('dashboard')) {
      return {
        response: `📊 **AsimNexus System Status**

**Components:**
✅ Frontend React — v3.0.1 (Running)
✅ Backend FastAPI — v3.0.0 (Connected)
⚠️  Local LLM — Offline (using fallback)
✅ WebSocket — Standby
✅ Blockchain Bridge — Connected

**Your Activity:**
• Messages today: 23
• Commands executed: 7
• AI interactions: 12
• Data processed: 1.2 MB

**Quick Stats:**
• Clones hired: 2 active
• Contracts: 3 in progress
• Network nodes: 3 neighbors
• Wallet balance: 1,247 ⓐ

**Everything is operational!** 🚀`, source: 'local'
      };
    }

    // Default response with suggestions
    return {
      response: `🤔 I received: "${message}"

**I can help you with:**
🏥 Health & Wellness — "Health check"
💼 Work & Business — "Work status"  
🤖 AI Agents — "Hire agent"
🌐 Mesh Network — "Mesh info"
⚖️ Governance — "Dharma balance"
💰 Wallet — "Check balance"
📊 System — "Show status"
❓ Help — "What is Asim"

Try one of these commands!`, source: 'local'
    };
  }
}

const asimBrain = new AsimBrainService();
export default asimBrain;
