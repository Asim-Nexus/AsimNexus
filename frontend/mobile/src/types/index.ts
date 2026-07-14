/**
 * AsimNexus Mobile — TypeScript type definitions
 */

export interface User {
    id: string;
    username: string;
    email: string;
    role: 'citizen' | 'company' | 'government' | 'admin';
    created_at?: string;
}

export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface HealthStatus {
    status: string;
    version?: string;
    uptime?: number;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
}

export interface WalletInfo {
    balance: number;
    currency: string;
    address?: string;
}

export interface IdentityInfo {
    did?: string;
    verified: boolean;
    level: number;
}

export interface NepalInfo {
    status: string;
    region: string;
    connectors: Record<string, number>;
}
