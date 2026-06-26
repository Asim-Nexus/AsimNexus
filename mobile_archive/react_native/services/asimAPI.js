/**
 * ASIMNEXUS API Service for React Native
 * Connects Mobile App to Backend API
 * API URL is configurable via config.js (defaults to port 8000 matching backend)
 */

import axios from 'axios';
import { API_BASE_URL } from '../config';

// Create axios instance with configurable base URL
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Client for ASIMNEXUS
const asimAPI = {
  // Health check
  async health() {
    try {
      const response = await api.get('/api/health');
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      return { error: error.message };
    }
  },

  // Chat
  async chat(message, useWorldOS = true) {
    try {
      const response = await api.post('/api/chat', {
        message,
        use_world_os: useWorldOS,
      });
      return response.data;
    } catch (error) {
      console.error('Chat error:', error);
      return { error: error.message };
    }
  },

  // World OS
  async getWorldOSStatus() {
    try {
      const response = await api.get('/api/world_os/status');
      return response.data;
    } catch (error) {
      console.error('World OS status error:', error);
      return { error: error.message };
    }
  },

  async getWorldOSAgents() {
    try {
      const response = await api.get('/api/world_os/agents');
      return response.data;
    } catch (error) {
      console.error('World OS agents error:', error);
      return { error: error.message };
    }
  },

  // Analytics
  async getAnalyticsOverview() {
    try {
      const response = await api.get('/api/analytics/overview');
      return response.data;
    } catch (error) {
      console.error('Analytics error:', error);
      return { error: error.message };
    }
  },

  // Security
  async getSecurityStatus() {
    try {
      const response = await api.get('/api/security/status');
      return response.data;
    } catch (error) {
      console.error('Security status error:', error);
      return { error: error.message };
    }
  },

  // Agents
  async getAgents() {
    try {
      const response = await api.get('/api/agents');
      return response.data;
    } catch (error) {
      console.error('Agents error:', error);
      return { error: error.message };
    }
  },

  // Founders
  async getFounders() {
    try {
      const response = await api.get('/api/founders');
      return response.data;
    } catch (error) {
      console.error('Founders error:', error);
      return { error: error.message };
    }
  },

  // Virtual Office
  async getVirtualOfficeStatus() {
    try {
      const response = await api.get('/api/virtual_office/status');
      return response.data;
    } catch (error) {
      console.error('Virtual Office status error:', error);
      return { error: error.message };
    }
  },

  async getVirtualOfficeRooms() {
    try {
      const response = await api.get('/api/virtual_office/rooms');
      return response.data;
    } catch (error) {
      console.error('Virtual Office rooms error:', error);
      return { error: error.message };
    }
  },
};

export default asimAPI;
