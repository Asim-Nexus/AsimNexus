/**
 * UniversalChat.jsx
 * Full-page chat using UnifiedChat component
 * All features: Clones, Voice, Files, Smart suggestions, Context awareness
 */
import React from 'react';
import UnifiedChat from '../shared/UnifiedChat';

export default function UniversalChat({ user, onCommand }) {
  return (
    <div style={{ height: '100%' }}>
      <UnifiedChat 
        user={user} 
        onCommand={onCommand} 
        compact={false}  // Full page mode
      />
    </div>
  );
}
