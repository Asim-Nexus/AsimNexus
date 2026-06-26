/**
 * ASIMNEXUS Mode Switching Hook
 * Switch between Citizen / Company / Government modes
 */

import { useState, useEffect, useCallback } from 'react';
import { personalAPI, authAPI } from './asimnexus';


const MODES = {
  CITIZEN: 'citizen',
  COMPANY: 'company',
  GOVERNMENT: 'government',
  HYBRID: 'hybrid'
};


export const useMode = () => {
  const [mode, setMode] = useState(MODES.CITIZEN);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Load mode from backend on mount
  useEffect(() => {
    const loadMode = async () => {
      try {
        const status = await personalAPI.getPersonalStatus();
        if (status.data?.mode) {
          setMode(status.data.mode);
        }
      } catch (error) {
        console.warn('Mode load failed, using default', error);
      }
    };
    loadMode();
  }, []);
  
  // Switch mode - update backend
  const switchMode = useCallback(async (newMode) => {
    setLoading(true);
    try {
      // Map mode to backend route
      const modeMap = {
        [MODES.CITIZEN]: '/api/personal/mode/citizen',
        [MODES.COMPANY]: '/api/personal/mode/company',
        [MODES.GOVERNMENT]: '/api/personal/mode/government',
        [MODES.HYBRID]: '/api/personal/mode/hybrid'
      };
      
      // Call backend to switch
      await fetch(modeMap[newMode] || modeMap[MODES.CITIZEN], {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      setMode(newMode);
      return true;
    } catch (error) {
      console.error('Mode switch failed:', error);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);
  
  const toggleAutopilot = useCallback(async (enabled) => {
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