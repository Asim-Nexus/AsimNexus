/**
 * ASIMNEXUS Mode Switcher
 * Switch between Citizen / Company / Government modes
 */

import React from 'react';
import { useAppContext } from '../contexts/AppContext';


const ModeSwitcher = () => {
  const { mode, modes, switchMode, loading } = useAppContext();
  
  const modeOptions = [
    { value: modes.CITIZEN, label: 'Citizen', icon: '👤', color: 'blue' },
    { value: modes.COMPANY, label: 'Company', icon: '🏢', color: 'green' },
    { value: modes.GOVERNMENT, label: 'Government', icon: '🏛️', color: 'purple' },
    { value: modes.HYBRID, label: 'Hybrid', icon: '🔄', color: 'orange' }
  ];
  
  return (
    <div className="mode-switcher">
      <div className="mode-label">Mode:</div>
      <div className="mode-buttons">
        {modeOptions.map(option => (
          <button
            key={option.value}
            onClick={() => switchMode(option.value)}
            disabled={loading || mode === option.value}
            className={`mode-btn mode-${option.color} ${mode === option.value ? 'active' : ''}`}
            title={option.label}
          >
            <span className="mode-icon">{option.icon}</span>
            <span className="mode-text">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};


export default ModeSwitcher;