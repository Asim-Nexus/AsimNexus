/**
 * AsimNexus Mobile — API Service
 * Connects React Native app to Python backend
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ApiResponse, HealthStatus, User, WalletInfo, NepalInfo } from '../types';

const BASE_URL = process.env.API_URL || 'http://localhost:8000';

class ApiService {
    private client: AxiosInstance;
    private token: string | null = null;

    constructor() {
        this.client = axios.create({
            baseURL: BASE_URL,
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' },
        });

        // Request interceptor — attach auth token
        this.client.interceptors.request.use(async (config) => {
            if (this.token) {
                config.headers.Authorization = `Bearer ${this.token}`;
            }
            return config;
        });

        // Response interceptor — handle 401
        this.client.interceptors.response.use(
            (response) => response,
            async (error) => {
                if (error.response?.status === 401) {
                    await AsyncStorage.removeItem('asimnexus_token');
                    this.token = null;
                }
                return Promise.reject(error);
            }
        );
    }

    setToken(token: string) {
        this.token = token;
    }

    // ── Auth ──────────────────────────────────────────────────────────────

    async login(email: string, password: string): Promise<ApiResponse<{ token: string; user: User }>> {
        const res = await this.client.post('/auth/login', { email, password });
        return res.data;
    }

    async register(username: string, email: string, password: string): Promise<ApiResponse<{ token: string; user: User }>> {
        const res = await this.client.post('/auth/register', { username, email, password });
        return res.data;
    }

    // ── Health ────────────────────────────────────────────────────────────

    async healthCheck(): Promise<ApiResponse<HealthStatus>> {
        const res = await this.client.get('/health/live');
        return res.data;
    }

    // ── Chat ──────────────────────────────────────────────────────────────

    async sendMessage(message: string, userId: string = 'anonymous'): Promise<ApiResponse> {
        const res = await this.client.post('/api/v1/chat', { message, user_id: userId });
        return res.data;
    }

    // ── Economy ───────────────────────────────────────────────────────────

    async getWallet(userId: string): Promise<ApiResponse<WalletInfo>> {
        const res = await this.client.get(`/api/finance/wallet/${userId}`);
        return res.data;
    }

    async getFinanceStatus(): Promise<ApiResponse> {
        const res = await this.client.get('/api/finance/status');
        return res.data;
    }

    // ── Identity ──────────────────────────────────────────────────────────

    async getIdentityStatus(): Promise<ApiResponse> {
        const res = await this.client.get('/api/blockchain/identity/status');
        return res.data;
    }

    async createDID(): Promise<ApiResponse> {
        const res = await this.client.post('/api/blockchain/identity/did/create');
        return res.data;
    }

    // ── Nepal ─────────────────────────────────────────────────────────────

    async getNepalStatus(): Promise<ApiResponse<NepalInfo>> {
        const res = await this.client.get('/api/nepal/status');
        return res.data;
    }

    async getNepalMinistries(): Promise<ApiResponse> {
        const res = await this.client.get('/api/nepal/ministries');
        return res.data;
    }

    async getNepalProvinces(): Promise<ApiResponse> {
        const res = await this.client.get('/api/nepal/provinces');
        return res.data;
    }

    // ── Government ────────────────────────────────────────────────────────

    async getGovernmentStatus(): Promise<ApiResponse> {
        const res = await this.client.get('/api/government/status');
        return res.data;
    }

    async applyEResidency(data: Record<string, any>): Promise<ApiResponse> {
        const res = await this.client.post('/api/government/eresidency/apply', data);
        return res.data;
    }

    // ── Mesh ──────────────────────────────────────────────────────────────

    async getMeshStatus(): Promise<ApiResponse> {
        const res = await this.client.get('/api/mesh/status');
        return res.data;
    }

    // ── Consensus ─────────────────────────────────────────────────────────

    async getConsensusStatus(): Promise<ApiResponse> {
        const res = await this.client.get('/api/consensus/status');
        return res.data;
    }
}

export const apiService = new ApiService();

export async function checkBackendHealth(): Promise<boolean> {
    try {
        const res = await apiService.healthCheck();
        return res?.success || res?.data?.status === 'ok';
    } catch {
        return false;
    }
}
