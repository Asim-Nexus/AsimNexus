// ASIMNEXUS Type Definitions - 2026 Advanced Types

export interface Founder {
  id: string;
  name: string;
  role: string;
  avatar: string;
  status: 'online' | 'offline' | 'busy';
  expertise: string[];
  cloneVersion: number;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'offline';
  tasks: number;
  capabilities: string[];
}

export interface SystemMetric {
  label: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  percentage: number;
}

export interface SecurityEvent {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  level: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: Date;
  source: string;
}

export interface Feature {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'core' | 'ai' | 'communication' | 'integration' | 'security' | 'analytics';
  route: string;
  hotkey: string;
}

export interface CompanyInfo {
  name: string;
  mission: string;
  vision: string;
  founded: Date;
  employees: number;
  revenue: string;
  projects: number;
  globalReach: string;
}

export interface WebhookEvent {
  id: string;
  name: string;
  url: string;
  status: 'active' | 'inactive';
  lastTriggered: Date;
  triggerCount: number;
}

export interface IoTDevice {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'maintenance';
  location: string;
  lastPing: Date;
  batteryLevel?: number;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  attachments?: string[];
  reactions?: string[];
}

export interface VoiceSession {
  id: string;
  caller: string;
  status: 'ringing' | 'connected' | 'ended';
  duration: number;
  quality: number;
  recording: boolean;
}

export interface SocialAccount {
  id: string;
  platform: 'whatsapp' | 'telegram' | 'twitter' | 'discord';
  username: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync: Date;
  unreadCount: number;
}

export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  accentColor: string;
  fontSize: 'small' | 'medium' | 'large';
  reducedMotion: boolean;
  highContrast: boolean;
}

export type UserMood = 'focused' | 'calm' | 'active' | 'stressed';

export type LayoutMode = 'mobile' | 'tablet' | 'desktop';

export interface AccessibilityConfig {
  screenReader: boolean;
  keyboardNavigation: boolean;
  highContrast: boolean;
  reducedMotion: boolean;
  fontSize: 'small' | 'medium' | 'large';
}

export type AnimationVariant = 'fade' | 'slide' | 'scale' | 'bounce' | 'flip';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
  dismissible: boolean;
}
