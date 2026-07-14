/**
 * ASIMNEXUS Core API — health, chat, brain, memory, database, cache, system operations
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const healthAPI = {
    check: (): Promise<AxiosResponse<ApiResponse<HealthStatus>>> => api.get('/health'),
};
export const chatAPI = {
    sendMessage: (message: string, userId: string = 'web_user'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/chat', { message, user_id: userId }),
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/status'),
    getSystemInfo: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/system/info'),
};
export const localLLMAPI = {
    getHealth: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/local-llm/health'),

    getModels: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('localLLMAPI.getModels() has no backend endpoint. Use chat.sendMessage() instead.');
        return api.get('/api/local-llm/health');
    },

    generate: (prompt: string, _modelId: string | null = null, _maxTokens: number = 512): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('localLLMAPI.generate() has no backend endpoint. Use chat.sendMessage() instead.');
        return api.post('/api/chat', { message: prompt, user_id: 'web_user' });
    },

    generateGemma: (prompt: string, _maxTokens: number = 512): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('localLLMAPI.generateGemma() has no backend endpoint. Use chat.sendMessage() instead.');
        return api.post('/api/chat', { message: prompt, user_id: 'web_user' });
    },
};
export const brainAPI = {
    process: (message: string, userId: string = 'web_user', mode: string = 'personal'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/brain/process', { message, user_id: userId, mode }),
    stream: (message: string, userId: string = 'web_user'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/brain/stream', { message, user_id: userId }),
};
export const memoryAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/memory/stats'),
    getRecent: (limit: number = 20): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/memory/recent', { params: { limit } }),
    search: (query: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/memory/search', { params: { q: query } }),
    deleteMessage: (messageId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.delete(`/api/memory/${messageId}`),
    getConversations: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/db/conversations/user/${userId}`),
};
export const databaseAPI = {
    createUser: (username: string, email: string | null = null, password: string | null = null, _preferences: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.createUser() deprecated. Use authAPI.register() instead.');
        return authAPI.register(email || `${username}@local`, email || `${username}@local`, password || 'default-pw');
    },

    getUser: (_userId: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.getUser() deprecated. Use authAPI.getMe() instead.');
        return api.get('/auth/me');
    },

    createConversation: (_userId: string, _title: string = 'New Chat', _modelUsed: string = 'qwen3-4b'): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.createConversation() has no backend endpoint.');
        return Promise.resolve({ data: { success: true, conversation_id: 'local-' + Date.now() } } as unknown as AxiosResponse<ApiResponse>);
    },

    getUserConversations: (userId: string, limit: number = 10): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/db/conversations/user/${userId}`, { params: { limit } }),

    addMessage: (_conversationId: string, _role: string, _content: string, _metadata: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.addMessage() deprecated. Messages saved automatically on chat.');
        return Promise.resolve({ data: { success: true, message_id: 'auto-' + Date.now() } } as unknown as AxiosResponse<ApiResponse>);
    },

    getMessages: (_conversationId: string, limit: number = 100): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.getMessages() deprecated. Use memoryAPI.getRecent() instead.');
        return api.get('/api/memory/recent', { params: { limit } });
    },

    storeApiKey: (userId: string, provider: string, apiKey: string, config: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/keys/update', { user_id: userId, provider, api_key: apiKey, ...config }),

    getApiKeys: (userId: string, provider: string | null = null): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/db/api-keys/${userId}${provider ? `?provider=${provider}` : ''}`),

    migrateApiKeys: (_adminPassword: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('databaseAPI.migrateApiKeys() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Migration not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    health: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/db/health'),
};
export const systemOperationsAPI = {
    createFolder: (_path: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.createFolder() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    deleteFolder: (_path: string, _recursive: boolean = false): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.deleteFolder() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    createFile: (_path: string, _content: string = ''): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.createFile() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    readFile: (_path: string, _maxLines: number = 100): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.readFile() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    writeFile: (_path: string, _content: string, _append: boolean = false): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.writeFile() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    listDirectory: (_path: string = '.'): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.listDirectory() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    searchFiles: (_pattern: string, _path: string = '.'): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.searchFiles() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    executeCommand: (_command: string, _timeout: number = 30): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('systemOperationsAPI.executeCommand() has no backend endpoint.');
        return Promise.resolve({ data: { success: false, message: 'Not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    getSystemInfo: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/system/info'),
};
export const cacheAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('cacheAPI.getStats() has no backend endpoint.');
        return api.get('/api/memory/stats');
    },

    clear: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('cacheAPI.clear() has no backend endpoint.');
        return Promise.resolve({ data: { success: true, message: 'No-op: cache clear not implemented in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },
};
