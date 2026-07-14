/**
 * ASIMNEXUS API Integration Layer — Shared Infrastructure
 * ========================================================
 * Provides the shared axios instance, interceptors, and auth helpers.
 *
 * All domain-specific API modules import `api` from this file.
 * Import domain APIs from the barrel index: `import { ... } from '../../api';`
 *
 * API host is configured via `REACT_APP_API_URL` or the unified API client.
 *
 * Auth flow: POST /auth/login and POST /auth/register expect JSON body with {email, password}.
 * Health: GET /health (aliased as /api/status, /api/db/health).
 * Chat: POST /api/chat (aliased as /chat, /llm/chat).
 */

import axios, {
    AxiosInstance,
    AxiosResponse,
    AxiosError,
    InternalAxiosRequestConfig,
} from 'axios';
import type { ApiResponse, User, HealthStatus, ApiError } from '../types';

// API base URL from environment variable (falls back to localhost:8000)
const BASE: string = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
    baseURL: BASE,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Request interceptor for authentication
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('asimnexus_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor for unified error handling
api.interceptors.response.use(
    (response: AxiosResponse) => {
        if (response.data && typeof response.data === 'object' && !response.data.success && !response.data.status) {
            response.data = { success: true, ...response.data };
        }
        return response;
    },
    (error: AxiosError) => {
        const status: number | undefined = error.response?.status;
        const data: unknown = error.response?.data;
        if (status === 401) {
            console.warn('[API] Unauthorized — clearing auth token');
            localStorage.removeItem('asimnexus_token');
            localStorage.removeItem('asimnexus_user');
        }
        const apiError: ApiError = {
            status,
            message:
                (data as Record<string, unknown>)?.detail as string ||
                (data as Record<string, unknown>)?.message as string ||
                error.message ||
                'Unknown API error',
            data: data || null,
            config: {
                url: error.config?.url,
                method: error.config?.method,
            },
        };
        console.warn(
            `[API] ${error.config?.method?.toString().toUpperCase() || '??'} ${error.config?.url || '??'} → ${status || 'ERR'}`,
            apiError.message
        );
        return Promise.reject(apiError);
    }
);

// ─── AUTH HELPERS ──────────────────────────────────────────────
export const getStoredToken = (): string | null =>
    localStorage.getItem('asimnexus_token');

export const getStoredUser = (): User | null => {
    try {
        return JSON.parse(localStorage.getItem('asimnexus_user') || 'null');
    } catch {
        return null;
    }
};

export const setAuth = (token: string, user: User): void => {
    localStorage.setItem('asimnexus_token', token);
    localStorage.setItem('asimnexus_user', JSON.stringify(user));
};

export const clearAuth = (): void => {
    localStorage.removeItem('asimnexus_token');
    localStorage.removeItem('asimnexus_user');
};

export default api;
