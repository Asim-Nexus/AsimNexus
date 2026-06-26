/**
 * ASIMNEXUS App Context
 * Global state for mode, user, and backend connection
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useMode } from '../hooks/useMode';
import { authAPI, healthAPI } from '../api/asimnexus';


const AppContext = createContext();


export const AppProvider = ({ children }) => {
  const modeState = useMode();
  const [user, setUser] = useState(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState({});
  
  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await healthAPI.check();
        setBackendConnected(true);
        setSystemStatus(response.data || {});
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
      setUser(JSON.parse(storedUser));
    }
  }, []);
  
  return (
    <AppContext.Provider value={{
      user,
      setUser,
      backendConnected,
      systemStatus,
      ...modeState,
    }}>
      {children}
    </AppContext.Provider>
  );
};


export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};