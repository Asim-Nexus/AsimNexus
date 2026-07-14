/**
 * ASIMNEXUS Mode Switching Hook
 * Switch between Citizen / Company / Government modes
 */

import { useState, useEffect, useCallback } from 'react';
import { personalAPI } from '../api/asimnexus';
import api from '../api/asimnexus';

interface ModeMap {
    CITIZEN: string;
    COMPANY: string;
    GOVERNMENT: string;
    HYBRID: string;
}

const MODES: ModeMap = {
    CITIZEN: 'citizen',
    COMPANY: 'company',
    GOVERNMENT: 'government',
    HYBRID: 'hybrid'
};

interface UseModeReturn {
    mode: string;
    modes: ModeMap;
    loading: boolean;
    user: unknown;
    switchMode: (newMode: string) => Promise<boolean>;
    toggleAutopilot: (enabled: boolean) => Promise<boolean>;
    isCitizen: boolean;
    isCompany: boolean;
    isGovernment: boolean;
    isHybrid: boolean;
}

export const useMode = (): UseModeReturn => {
    const [mode, setMode] = useState<string>(MODES.CITIZEN);
    const [user] = useState<unknown>(null);
    const [loading, setLoading] = useState<boolean>(false);

    // Load mode from backend on mount
    useEffect(() => {
        const loadMode = async () => {
            try {
                const status = await personalAPI.getPersonalStatus();
                const data = status.data as unknown as Record<string, unknown>;
                if (data?.mode) {
                    setMode(data.mode as string);
                }
            } catch (error) {
                console.warn('Mode load failed, using default', error);
            }
        };
        loadMode();
    }, []);

    // Switch mode - update backend
    const switchMode = useCallback(async (newMode: string): Promise<boolean> => {
        setLoading(true);
        try {
            // Map mode to backend route
            const modeMap: Record<string, string> = {
                [MODES.CITIZEN]: '/api/personal/mode/citizen',
                [MODES.COMPANY]: '/api/personal/mode/company',
                [MODES.GOVERNMENT]: '/api/personal/mode/government',
                [MODES.HYBRID]: '/api/personal/mode/hybrid'
            };

            // Call backend to switch
            await api.post(modeMap[newMode] || modeMap[MODES.CITIZEN]);

            setMode(newMode);
            return true;
        } catch (error) {
            console.error('Mode switch failed:', error);
            return false;
        } finally {
            setLoading(false);
        }
    }, []);

    const toggleAutopilot = useCallback(async (_enabled: boolean): Promise<boolean> => {
        try {
            await personalAPI.agentModeOn();
            return true;
        } catch (error) {
            console.error('Autopilot toggle failed:', error);
            return false;
        }
    }, []);

    return {
        mode,
        modes: MODES,
        loading,
        user,
        switchMode,
        toggleAutopilot,
        isCitizen: mode === MODES.CITIZEN,
        isCompany: mode === MODES.COMPANY,
        isGovernment: mode === MODES.GOVERNMENT,
        isHybrid: mode === MODES.HYBRID,
    };
};
