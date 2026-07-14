/**
 * GovernanceChatService.ts
 * ========================
 * Extracted command processing logic for GovernanceChat.
 * Provides testable, reusable service functions for all governance chat commands.
 *
 * Command categories:
 * - Power Balance (51/49)
 * - Policies (approve, list)
 * - Veto (issue, check)
 * - Emergency (declare, resolve)
 * - Audit Log
 * - Dharma Check
 * - Enterprise Licenses (register, list)
 * - Compliance (check, log)
 * - Stakeholder Actions (propose, list, approve)
 * - Agent Mode (activate, status)
 * - System Status / Stats
 * - Help
 */

import { governanceAPI, enterpriseAPI, stakeholderAPI } from '../api/asimnexus';

// ─── Types ───────────────────────────────────────────────────────────────────

export type ChatMode = 'citizen' | 'government' | 'company';

export interface GovernanceAction {
    type: string;
    status: 'pending' | 'executing' | 'success' | 'error';
    result?: Record<string, unknown>;
    error?: string;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    action?: GovernanceAction;
}

export interface CommandResult {
    content: string;
    action?: GovernanceAction;
}

export interface GovernanceChatServiceConfig {
    user?: Record<string, unknown>;
    mode: ChatMode;
}

// ─── Mode Configuration ──────────────────────────────────────────────────────

export const MODE_CONFIG: Record<ChatMode, { label: string; color: string; icon: string }> = {
    citizen: { label: 'Citizen', color: '#8b5cf6', icon: '👤' },
    government: { label: 'Government', color: '#10b981', icon: '🏛️' },
    company: { label: 'Enterprise', color: '#3b82f6', icon: '🏢' },
};

export const QUICK_ACTIONS: Record<ChatMode, { label: string; cmd: string }[]> = {
    citizen: [
        { label: 'Check Power Balance', cmd: 'Show me the current 51/49 power balance' },
        { label: 'My Contracts', cmd: 'List my active agent contracts' },
        { label: 'Propose Action', cmd: 'I want to propose a new community action' },
        { label: 'Agent Mode', cmd: 'Enable agent mode for 5 days' },
    ],
    government: [
        { label: 'Approve Policy', cmd: 'Show pending policies for approval' },
        { label: 'Issue Veto', cmd: 'I need to issue a government veto' },
        { label: 'Emergency', cmd: 'Declare a government emergency' },
        { label: 'Audit Log', cmd: 'Show the latest governance audit log' },
    ],
    company: [
        { label: 'Register License', cmd: 'Register a new enterprise license' },
        { label: 'Check Compliance', cmd: 'Check compliance for an action' },
        { label: 'Hire Agent', cmd: 'Hire an AI agent for 30 days' },
        { label: 'License Status', cmd: 'Show my enterprise licenses' },
    ],
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function formatJson(data: unknown): string {
    return `\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
}

function extractData(res: { data?: { data?: unknown } | unknown }): unknown {
    return (res.data as Record<string, unknown>)?.data || res.data;
}

// ─── Command Processors ──────────────────────────────────────────────────────

/**
 * Process a power balance check command.
 */
async function processPowerBalance(): Promise<CommandResult> {
    const res = await governanceAPI.getBalance();
    const data = extractData(res);
    return {
        content: `📊 **Power Balance Report**\n${formatJson(data || 'No data available')}`,
        action: { type: 'check_balance', status: 'success', result: (data || {}) as Record<string, unknown> },
    };
}

/**
 * Process a policy-related command.
 */
async function processPolicy(cmd: string): Promise<CommandResult> {
    const lower = cmd.toLowerCase();
    if (lower.includes('approve') || lower.includes('pending')) {
        const res = await governanceAPI.getPolicies();
        const policies = extractData(res);
        return {
            content: `📋 **Pending Policies**\n${formatJson(policies || {})}`,
            action: { type: 'list_policies', status: 'success', result: (policies || {}) as Record<string, unknown> },
        };
    }
    return {
        content: `To work with policies, try:\n- "Show pending policies"\n- "Approve policy [id]"`,
    };
}

/**
 * Process a veto-related command.
 */
async function processVeto(): Promise<CommandResult> {
    const res = await governanceAPI.getAuditLog();
    const log = extractData(res);
    return {
        content: `⚖️ **Veto System**\nRecent audit entries:\n${formatJson(log || {})}`,
        action: { type: 'veto_check', status: 'success', result: (log || {}) as Record<string, unknown> },
    };
}

/**
 * Process an emergency declaration command.
 */
async function processEmergency(cmd: string, config: GovernanceChatServiceConfig): Promise<CommandResult> {
    const lower = cmd.toLowerCase();
    if (lower.includes('declare')) {
        const res = await governanceAPI.declareEmergency({
            initiated_by: (config.user?.display_name as string) || 'unknown',
            reason: cmd,
        } as unknown as string);
        return {
            content: `🚨 **Emergency Declared**\n${formatJson(res.data || {})}`,
            action: { type: 'declare_emergency', status: 'success', result: (res.data || {}) as unknown as Record<string, unknown> },
        };
    }
    return {
        content: `To declare an emergency, say: "Declare emergency because [reason]"`,
    };
}

/**
 * Process an audit log command.
 */
async function processAudit(): Promise<CommandResult> {
    const res = await governanceAPI.getAuditLog();
    const log = extractData(res);
    return {
        content: `📜 **Governance Audit Log**\n${formatJson(log || {})}`,
        action: { type: 'audit_log', status: 'success', result: (log || {}) as Record<string, unknown> },
    };
}

/**
 * Process a Dharma check command.
 */
async function processDharmaCheck(cmd: string, config: GovernanceChatServiceConfig): Promise<CommandResult> {
    const actionText = cmd.replace(/check|dharma|action/gi, '').trim() || 'default_action';
    const res = await governanceAPI.dharmaCheck({
        action: actionText,
        context: { initiated_by: (config.user?.display_name as string) || 'user' },
    } as unknown as string);
    return {
        content: `🕉️ **Dharma Veto Check**\n${formatJson(res.data || {})}`,
        action: { type: 'dharma_check', status: 'success', result: (res.data || {}) as unknown as Record<string, unknown> },
    };
}

/**
 * Process an enterprise license command.
 */
async function processLicense(cmd: string): Promise<CommandResult> {
    const lower = cmd.toLowerCase();
    if (lower.includes('register')) {
        return {
            content: `📝 To register a license, please provide:\n1. Organization name\n2. Tier (free/starter/business/enterprise)\n3. Jurisdiction\n\nOr use the Enterprise Dashboard for the full form.`,
        };
    }
    const res = await enterpriseAPI.getLicenses();
    const licenses = extractData(res);
    return {
        content: `📋 **Enterprise Licenses**\n${formatJson(licenses || {})}`,
        action: { type: 'list_licenses', status: 'success', result: (licenses || {}) as Record<string, unknown> },
    };
}

/**
 * Process a compliance check command.
 */
async function processCompliance(): Promise<CommandResult> {
    const res = await enterpriseAPI.getComplianceLog();
    const log = extractData(res);
    return {
        content: `✅ **Compliance Log**\n${formatJson(log || {})}`,
        action: { type: 'compliance_log', status: 'success', result: (log || {}) as Record<string, unknown> },
    };
}

/**
 * Process a stakeholder action command.
 */
async function processStakeholder(cmd: string): Promise<CommandResult> {
    const lower = cmd.toLowerCase();
    if (lower.includes('propose') || lower.includes('new')) {
        return {
            content: `🤝 To propose a new stakeholder action, please specify:\n1. Category (policy/license/contract/mode_change/emergency/amendment/compliance/audit)\n2. Description of the action\n3. Any additional details\n\nExample: "Propose a policy to reduce carbon emissions by 50%"`,
        };
    }
    const res = await stakeholderAPI.listActions();
    const actions = extractData(res);
    return {
        content: `📋 **Stakeholder Actions**\n${formatJson(actions || {})}`,
        action: { type: 'list_actions', status: 'success', result: (actions || {}) as Record<string, unknown> },
    };
}

/**
 * Process an agent mode command.
 */
async function processAgentMode(cmd: string): Promise<CommandResult> {
    const lower = cmd.toLowerCase();
    const duration = lower.includes('30') ? 30 : lower.includes('15') ? 15 : 5;
    return {
        content: `🤖 **Agent Mode Activation**\n\nTo activate agent mode for ${duration} days, use the Agent Mode panel or the API:\n\`POST /api/agent/mode/on\` with duration: ${duration}\n\nVisit the Agent Mode dashboard for full controls.`,
        action: { type: 'agent_mode', status: 'success' },
    };
}

/**
 * Process a system status/stats command.
 */
async function processStats(): Promise<CommandResult> {
    const [govStats, entStats, stakeStats] = await Promise.all([
        governanceAPI.getStats().catch(() => ({ data: { data: { error: 'unavailable' } } })),
        enterpriseAPI.getStats().catch(() => ({ data: { data: { error: 'unavailable' } } })),
        stakeholderAPI.getStats().catch(() => ({ data: { data: { error: 'unavailable' } } })),
    ]);

    const govData = extractData(govStats);
    const entData = extractData(entStats);
    const stakeData = extractData(stakeStats);

    return {
        content: `📊 **Governance System Status**\n\n**🏛️ Government Layer:**\n${formatJson(govData)}\n\n**🏢 Enterprise Layer:**\n${formatJson(entData)}\n\n**🤝 Stakeholder Coordinator:**\n${formatJson(stakeData)}`,
        action: { type: 'system_status', status: 'success' },
    };
}

/**
 * Process a help command.
 */
async function processHelp(): Promise<CommandResult> {
    return {
        content: `🔍 **Available Commands**\n\n**🏛️ Government (51%):**\n- "Show power balance"\n- "Show pending policies"\n- "Issue a veto"\n- "Declare emergency"\n- "Show audit log"\n- "Check action with Dharma"\n\n**🏢 Enterprise (49%):**\n- "Show enterprise licenses"\n- "Check compliance"\n- "Register a license"\n\n**👤 Citizen (100%):**\n- "Propose a stakeholder action"\n- "Enable agent mode for 5/15/30 days"\n- "Show system status"\n\n**Quick tip:** Use the mode selector above to switch between Citizen/Government/Company views!`,
    };
}

/**
 * Process a fallback (unrecognized) command.
 */
async function processFallback(cmd: string): Promise<CommandResult> {
    return {
        content: `I understand you're asking about: "${cmd}"\n\nI can help with governance actions like checking power balance, policies, vetos, enterprise licenses, compliance, and stakeholder coordination. Try saying "help" to see all available commands, or use one of the quick action buttons above.`,
    };
}

// ─── Main Command Router ─────────────────────────────────────────────────────

/**
 * Route a command string to the appropriate processor based on keywords.
 * Returns the command result with formatted content and optional action metadata.
 */
export async function processCommand(cmd: string, config: GovernanceChatServiceConfig): Promise<CommandResult> {
    const lower = cmd.toLowerCase().trim();

    try {
        // ── Power Balance ──
        if (lower.includes('power balance') || lower.includes('51/49') || lower.includes('balance')) {
            return await processPowerBalance();
        }

        // ── Policies ──
        if (lower.includes('policy') || lower.includes('policies')) {
            return await processPolicy(cmd);
        }

        // ── Veto ──
        if (lower.includes('veto')) {
            return await processVeto();
        }

        // ── Emergency ──
        if (lower.includes('emergency')) {
            return await processEmergency(cmd, config);
        }

        // ── Audit ──
        if (lower.includes('audit')) {
            return await processAudit();
        }

        // ── Dharma Check ──
        if (lower.includes('dharma') || lower.includes('check action')) {
            return await processDharmaCheck(cmd, config);
        }

        // ── Enterprise Licenses ──
        if (lower.includes('license') || lower.includes('licenses')) {
            return await processLicense(cmd);
        }

        // ── Compliance ──
        if (lower.includes('compliance') || lower.includes('compliant')) {
            return await processCompliance();
        }

        // ── Stakeholder Actions ──
        if (lower.includes('stakeholder') || lower.includes('propose action') || lower.includes('community action')) {
            return await processStakeholder(cmd);
        }

        // ── Agent Mode ──
        if (lower.includes('agent mode') || lower.includes('enable agent') || lower.includes('activate agent')) {
            return await processAgentMode(cmd);
        }

        // ── Stats / Status ──
        if (lower.includes('stats') || lower.includes('status') || lower.includes('health')) {
            return await processStats();
        }

        // ── Help ──
        if (lower.includes('help') || lower.includes('what can you') || lower.includes('commands')) {
            return await processHelp();
        }

        // ── Fallback ──
        return await processFallback(cmd);

    } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        return {
            content: `❌ **Error:** ${errorMsg}\n\nThe backend may be unavailable. Try again later or use the dashboard panels directly.`,
            action: { type: 'error', status: 'error', error: errorMsg },
        };
    }
}

/**
 * Create a ChatMessage from a CommandResult.
 */
export function createMessage(role: ChatMessage['role'], result: CommandResult): ChatMessage {
    return {
        id: generateId(),
        role,
        content: result.content,
        timestamp: Date.now(),
        action: result.action,
    };
}

/**
 * Create a welcome message for the chat.
 */
export function createWelcomeMessage(): ChatMessage {
    return {
        id: 'welcome',
        role: 'assistant',
        content: `👋 Welcome to **AsimNexus Governance Chat**!\n\nI can help you interact with the **51% Government / 49% Enterprise / 100% User** ecosystem. Try one of the quick actions below or type your request.`,
        timestamp: Date.now(),
    };
}
