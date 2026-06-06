/**
 * ASIMNEXUS Chat - Founder Selector Component
 * Group chat founder selection with consolidated roles
 */

import React, { memo } from 'react';

const FounderSelector = ({
  founders,
  selectedFounders,
  setSelectedFounders,
  autopilotMode,
}) => {
  return (
    <div className="founder-selector">
      <div className="founder-header">
        <span className="founder-label">5 Optimized Founders (from 15):</span>
        <div className="founder-stats">
          <span className="online-count">
            {founders.filter(f => f.online).length} Online
          </span>
          {autopilotMode && <span className="autopilot-indicator">🤖 Autonomous</span>}
        </div>
      </div>
      <div className="founder-tags">
        {founders.map(founder => (
          <button
            key={founder.id}
            className={`founder-tag ${selectedFounders.includes(founder.id) ? 'selected' : ''} ${!founder.online ? 'offline' : ''}`}
            onClick={() => {
              if (selectedFounders.includes(founder.id)) {
                setSelectedFounders(selectedFounders.filter(f => f !== founder.id));
              } else {
                setSelectedFounders([...selectedFounders, founder.id]);
              }
            }}
          >
            <span className="founder-avatar">{founder.avatar}</span>
            <span className="founder-info">
              <span className="founder-name">{founder.name}</span>
              <span className="founder-role">{founder.role}</span>
              <span className="founder-specialization">{founder.specialization}</span>
            </span>
            <span className={`status-dot ${founder.online ? 'online' : 'offline'}`} />
          </button>
        ))}
      </div>
      <div className="founder-actions">
        <button
          className="select-all-button"
          onClick={() => setSelectedFounders(founders.map(f => f.id))}
        >
          Select All
        </button>
        <button
          className="clear-selection-button"
          onClick={() => setSelectedFounders([])}
        >
          Clear Selection
        </button>
      </div>
    </div>
  );
};

export default memo(FounderSelector);
