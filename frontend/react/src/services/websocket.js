/**
 * WebSocket Service for Real-time Updates
 * =========================================
 * Delegates to WebSocketService.js (native WebSocket with exponential backoff).
 * Kept for backward compatibility — all new code should import from WebSocketService.js directly.
 *
 * @see ./WebSocketService.js for the full implementation
 */

import _wsService from './WebSocketService';

// Re-export the singleton instance
export const wsService = _wsService;
export default _wsService;
