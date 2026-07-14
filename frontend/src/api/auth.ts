/**
 * ASIMNEXUS Authentication API — login, register, token management
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 *
 * Auth helpers (getStoredToken, getStoredUser, setAuth, clearAuth)
 * are defined in ./asimnexus.ts and re-exported via the barrel index.
 * Import them from '../../api' directly.
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse } from '../types';
import { setAuth } from './asimnexus';

export const authAPI = {
    login: (email: string, password: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/auth/login', { email, password }).then((res: AxiosResponse) => {
            if (res.data?.success) {
                setAuth(res.data.token, res.data.user);
            }
            return res.data;
        }),

    register: (
        displayName: string,
        email: string,
        password: string,
        phone: string | null = null,
        countryCode: string = 'NP',
        nationalId: string | null = null
    ): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/auth/register', {
            email, password,
            display_name: displayName,
            phone,
            country_code: countryCode,
            national_id: nationalId,
        }).then((res: AxiosResponse) => {
            if (res.data?.success) {
                setAuth(res.data.token, res.data.user);
            }
            return res.data;
        }),

    getMe: (): Promise<AxiosResponse<ApiResponse>> => api.get('/auth/me'),
};
