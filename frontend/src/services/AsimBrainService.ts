/**
 * AsimBrainService.ts
 * Phase 3: AI integration with AsimBrain (core/asim_brain.py)
 */

import api, { getStoredToken } from '../api/asimnexus';

interface ProcessResult {
    response: string;
    source: string;
}

interface StreamContext {
    mode?: string;
    [key: string]: unknown;
}

class AsimBrainService {
    constructor() {
        // Initial state
    }

    async processMessage(message: string, context: Record<string, unknown> = {}): Promise<ProcessResult> {
        console.log('[AsimBrain] Processing message:', message.substring(0, 50));

        // Check for tool command pattern: "tool.name: {params}"
        const toolMatch = message.match(/^(\w+(?:\.\w+)+)\s*:\s*(\{.*\})?/);
        if (toolMatch) {
            const toolId = toolMatch[1];
            const paramsStr = toolMatch[2] || '{}';
            try {
                const params = JSON.parse(paramsStr);
                const result = await api.post('/api/tools/execute', { tool_id: toolId, parameters: params, agent_name: 'AutoModeAgent' });
                if (result.data) {
                    return {
                        response: `🌌 **Asim**\n\n**Tool Result for \`${toolId}\`:**\n\`\`\`\n${JSON.stringify(result.data.result, null, 2)}\n\`\`\``,
                        source: 'asim_nexus'
                    };
                }
            } catch (error: unknown) {
                const errMsg = error instanceof Error ? error.message : String(error);
                return { response: `🌌 **Asim**\n\nError: ${errMsg}`, source: 'asim_nexus' };
            }
        }

        // Try direct backend API first
        try {
            const response = await api.post('/api/brain/process', {
                message,
                context: { ...context, timestamp: Date.now(), source: 'asim_orb' },
            });

            if (response.data) {
                const data = response.data;
                console.log('[AsimBrain] Backend response received');
                return { response: data.response || '', source: data.source || 'backend' };
            }
        } catch (error) {
            console.log('[AsimBrain] Backend unavailable, using local fallback');
        }

        // Fallback: Local processing
        return this.localProcess(message, context);
    }

    async *streamMessage(message: string, context: StreamContext = {}): AsyncGenerator<string> {
        try {
            const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const token = getStoredToken();
            const response = await fetch(`${API_BASE}/api/brain/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),
                },
                body: JSON.stringify({
                    message,
                    context,
                    mode: context.mode || 'personal',
                    streaming: true,
                }),
            });

            if (!response.body) {
                yield '[AI connection failed. No response body.]';
                return;
            }

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
                        } catch {
                            // Skip malformed JSON lines
                        }
                    }
                }
            }
        } catch (error) {
            yield '[AI connection failed. Using local mode.]';
        }
    }

    localProcess(message: string, _context: Record<string, unknown> = {}): ProcessResult {
        const lower = message.toLowerCase();

        // 🏥 HEALTH & WELLNESS
        if (lower.includes('health') || lower.includes('swasthya') || lower.includes('doctor') || lower.includes('स्वास्थ्य')) {
            return {
                response: `🌌 **Asim**

**स्वास्थ्य ड्यासबोर्ड**

• रकतचाप: 120/80 mmHg (साधारण)
• हृदयगति: 72 bpm (विश्राम)
• निद्रा: 7.5 घण्टा
• आजको चरण: 8,432

**सिफारिसहरू:**
• 2L पानी प drinking
• 30 मिनेट मेडिटेसन suggests`, source: 'asim_nexus'
            };
        }

        // 💼 WORK & ENTERPRISE
        if (lower.includes('work') || lower.includes('company') || lower.includes('business') || lower.includes('job') || lower.includes('काम')) {
            return {
                response: `🌌 **Asim**

**काम मोड**

• अनुबन्धहरू: ३ सक्रिय
• माइलो: २/५ पूरा
• आमदनी: $20,800 यस महिना
• एजेन्टहरू काम गरिरहेका छन्

**Actions:**
• /contracts — अनुबन्धहरू हेर्नुहोस्
• /hire — एजेन्ट हायर गर्नुहोस्`, source: 'asim_nexus'
            };
        }

        // 🤖 AI AGENTS & CLONES
        if (lower.includes('agent') || lower.includes('clone') || lower.includes('hire') || lower.includes('bot') || lower.includes('एजेन्ट')) {
            return {
                response: `🌌 **Asim**

**उपलब्ध AI एजेन्टहरू**
1. 💻 Tech Architect — $50/दिन
2. 🥷 Data Engineer — $40/दिन
3. 🛡️ Security Sentinel — $35/दिन
4. ❤️ Health Sage — $30/दिन

**Commands:**
• /hire — एजेन्ट हायर गर्नुहोस्
• /pause — एजेन्ट रोक्नुहोस्`, source: 'asim_nexus'
            };
        }

        // 🌐 MESH NETWORK
        if (lower.includes('mesh') || lower.includes('network') || lower.includes('connect') || lower.includes('wifi') || lower.includes('जाल')) {
            return {
                response: `🌌 **Asim**

**मेष जाल स्थिति**

• नोडहरू: ३ जडान
• आज: ४५ MB अपलोड, १२८ MB डाउनलोड
• स्थिति: अनलाइन & सिङ्क

Actions: /scan — नेटवर्क स्क्यान गर्नुहोस्`, source: 'asim_nexus'
            };
        }

        // ⚖️ DHARMA / GOVERNANCE
        if (lower.includes('dharma') || lower.includes('balance') || lower.includes('vote') || lower.includes('governance') || lower.includes('धर्म')) {
            return {
                response: `🌌 **Asim**

**धर्म गवर्नेन्स**

• सन्तुलन स्कोर: 94.2%
• गिनी सिद्धान्त: 0.32
• अन्तिम मतदान: सफल

• Actions: /Vote · /View proposals`, source: 'asim_nexus'
            };
        }

        // 💰 WALLET / FINANCE
        if (lower.includes('money') || lower.includes('wallet') || lower.includes('balance') || lower.includes('payment') || lower.includes('send') || lower.includes('पैसा')) {
            return {
                response: `🌌 **Asim**

**Asim वालेट**

• ASIM टोकनहरू: 1,247.50 ⓐ
• USDC: $450.00
• ETH: 0.42 Ξ

• Actions: /Send · /Receive · /History`, source: 'asim_nexus'
            };
        }

        // 🆘 HELP / WHAT IS ASIM
        if (lower.includes('help') || lower.includes('what is asim') || lower.includes('about') || lower.includes('guide') || lower.includes('मद्दत')) {
            return {
                response: `🌌 **AsimNexus World OS**

म तपाईंको व्यक्तिगत AI सहयोगी Asim हुँ।

**म के गर्न सक्छु:**
• 🏥 स्वास्थ्य प्रबन्धन
• 💼 व्यवसाय AI एजेन्टहरूसँग
• 🤖 विशेषज्ञ एजेन्टहरू हायर गर्नुहोस्
• 🌐 मेष नेटवर्कमा जडान
• ⚖️ गवर्नेन्समा सहभागी
• 💰 भुक्तानीहरू

Try: "Health check" | "Work status" | "Hire agent" | "Mesh info"`, source: 'asim_nexus'
            };
        }

        // 📊 SYSTEM STATUS
        if (lower.includes('status') || lower.includes('system') || lower.includes('info') || lower.includes('dashboard') || lower.includes('स्थिति')) {
            return {
                response: `🌌 **Asim**

**प्रणाली स्थिति**
• Frontend React — v3.0.1 (चलिरहेको)
• Backend FastAPI — v3.0.0 (जडान)
• WebSocket — तयार
• Blockchain — तयार`, source: 'asim_nexus'
            };
        }

        // Default response with suggestions
        return {
            response: `🌌 **Asim**

Received: "${message}"

म तपाईंलाई कसरी मद्दत गर्न सक्छु?

🏥 Health · 💼 Work · 🤖 Agents · 🌐 Mesh · ⚖️ Governance · 💰 Wallet`, source: 'asim_nexus'
        };
    }
}

const asimBrain = new AsimBrainService();
export default asimBrain;
