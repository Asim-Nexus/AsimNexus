// ASIMNEXUS Type Definitions - 2026 Advanced Types

// ─── Core Domain Types ──────────────────────────────────────────

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

// ─── API Layer Types ────────────────────────────────────────────

/** Generic API response wrapper */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  detail?: string;
  status?: string;
}

/** Authentication response from backend */
export interface AuthResponse {
  token: string;
  user: User;
}

/** User model */
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'founder';
  avatar?: string;
  createdAt?: string;
}

/** Backend health check response */
export interface HealthStatus {
  status: string;
  version?: string;
  uptime?: number;
  database?: string;
  redis?: string;
}

/** Structured API error */
export interface ApiError {
  status?: number;
  message: string;
  data: unknown;
  config: {
    url?: string;
    method?: string;
  };
}

// ─── Chat Types ─────────────────────────────────────────────────

/** Chat message as used by ChatContext */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  ts: number;
  attachments?: string[];
}

/** Clone selection option */
export interface CloneOption {
  id: string;
  icon: string;
  name: string;
  color: string;
}

/** Chat context value type */
export interface ChatContextValue {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  addMessage: (msg: ChatMessage) => void;
  loading: boolean;
  updateLoading: (val: boolean) => void;
  selectedClone: CloneOption;
  setSelectedClone: React.Dispatch<React.SetStateAction<CloneOption>>;
  clearMessages: () => void;
}

// ─── WebSocket Types ────────────────────────────────────────────

/** WebSocket connection states */
export enum WsConnectionState {
  CONNECTING = 0,
  OPEN = 1,
  CLOSING = 2,
  CLOSED = 3,
}

/** WebSocket event types */
export type WsEventType =
  | 'chat_message'
  | 'ai_stream_request'
  | 'ai_stream_chunk'
  | 'ai_stream_end'
  | 'system_notification'
  | 'connection_status'
  | 'error';

/** Generic WebSocket message envelope */
export interface WsMessage {
  type: WsEventType;
  payload: unknown;
  id?: string;
  timestamp?: number;
}

/** WebSocket message handler callback */
export type WsMessageHandler = (data: WsMessage) => void;

/** WebSocket endpoint configuration */
export interface WsEndpointConfig {
  url: string;
  onMessage: WsMessageHandler;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

// ─── Theme Types ────────────────────────────────────────────────

/** Theme color palette */
export interface Theme {
  bg: string;
  accent: string;
  text: string;
  card: string;
}

/** Available theme names */
export type ThemeName = 'deep-space' | 'aurora' | 'government' | 'corporate' | 'medical' | 'minimal';

// ─── App Context Types ──────────────────────────────────────────

/** App context value type */
export interface AppContextValue {
  user: User | null;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
  backendConnected: boolean;
  systemStatus: Record<string, unknown>;
  mode: string;
  setMode: (mode: string) => void;
}

// ─── Streaming / SSE Types ──────────────────────────────────────

/** SSE stream chunk */
export interface StreamChunk {
  text: string;
  done: boolean;
  error?: string;
}

/** Options for processing a message */
export interface ProcessMessageOptions {
  clone?: string;
  mode?: string;
  stream?: boolean;
  context?: Record<string, unknown>;
}

// ─── Component Prop Types ───────────────────────────────────────

/** Generic hub page props */
export interface HubPageProps {
  user?: User;
}

/** Sidebar navigation item */
export interface NavItem {
  id: string;
  label: string;
  icon: string;
  route: string;
  badge?: number;
}

/** Tab configuration for hub pages */
export interface TabConfig {
  id: string;
  label: string;
  icon: string;
  component: React.ComponentType<unknown>;
}
