/**
 * ASIMNEXUS App Context
 * Global state for mode, user, and backend connection
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMode } from '../hooks/useMode';

interface SystemStatus {
    [key: string]: unknown;
}

interface AppContextValue {
    user: unknown;
    setUser: React.Dispatch<React.SetStateAction<unknown>>;
    backendConnected: boolean;
    systemStatus: SystemStatus;
    mode: string;
    modes: { CITIZEN: string; COMPANY: string; GOVERNMENT: string; HYBRID: string };
    loading: boolean;
    switchMode: (newMode: string) => Promise<boolean>;
    toggleAutopilot: (enabled: boolean) => Promise<boolean>;
    isCitizen: boolean;
    isCompany: boolean;
    isGovernment: boolean;
    isHybrid: boolean;
}

const AppContext = createContext<AppContextValue | null>(null);

interface AppProviderProps {
    children: ReactNode;
}

export const AppProvider = ({ children }: AppProviderProps) => {
    const modeState = useMode();
    const [appUser, setAppUser] = useState<unknown>(null);
    const [backendConnected, setBackendConnected] = useState<boolean>(false);
    const [systemStatus, setSystemStatus] = useState<SystemStatus>({});

    // Check backend connection on mount
    useEffect(() => {
        const checkBackend = async () => {
            try {
                const { healthAPI } = await import('../api/asimnexus');
                const response = await healthAPI.check();
                setBackendConnected(true);
                setSystemStatus(response.data as unknown as SystemStatus || {});
            } catch (error) {
                setBackendConnected(false);
            }
        };
        checkBackend();
        const interval = setInterval(checkBackend, 30000); // Check every 30s
        return () => clearInterval(interval);
    }, []);

    // Load user on mount
    useEffect(() => {
        const storedUser = localStorage.getItem('asimnexus_user');
        if (storedUser) {
            try {
                setAppUser(JSON.parse(storedUser));
            } catch {
                // ignore parse errors
            }
        }
    }, []);

    // Separate modeState user from app user to avoid duplicate key
    const { user: _modeUser, ...restModeState } = modeState;

    return (
        <AppContext.Provider value={{
            user: appUser,
            setUser: setAppUser,
            backendConnected,
            systemStatus,
            ...restModeState,
        }}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = (): AppContextValue => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within AppProvider');
    }
    return context;
};
