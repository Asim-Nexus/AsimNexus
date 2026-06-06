/**
 * NativeBridge.js
 * Phase 5: Cross-platform native integration
 * Bridges web frontend with native OS capabilities
 */

// Platform detection
const isAndroid = /Android/.test(navigator.userAgent);
const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
const isWindows = /Windows/.test(navigator.userAgent);
const isLinux = /Linux/.test(navigator.userAgent) && !isAndroid;
const isMac = /Mac/.test(navigator.userAgent) && !isIOS;

const PLATFORM = isAndroid ? 'android' : isIOS ? 'ios' : isWindows ? 'windows' : isLinux ? 'linux' : isMac ? 'macos' : 'web';

class NativeBridge {
  constructor() {
    this.platform = PLATFORM;
    this.nativeAPI = null;
    this.permissions = {};
    this.initialized = false;
  }

  init() {
    if (this.initialized) return;
    
    try {
      console.log(`[NativeBridge] Platform: ${this.platform}`);
      
      switch (this.platform) {
      case 'android':
        this.initAndroid();
        break;
      case 'ios':
        this.initIOS();
        break;
      case 'windows':
        this.initWindows();
        break;
      case 'linux':
        this.initLinux();
        break;
      case 'macos':
        this.initMacOS();
        break;
      default:
        this.initWeb();
    }
      
      this.initialized = true;
    } catch (e) {
      console.warn('[NativeBridge] Init failed:', e);
      this.initWeb();
      this.initialized = true;
    }
  }

  // Android implementation
  initAndroid() {
    // Check for React Native WebView bridge
    if (window.ReactNativeWebView) {
      this.nativeAPI = window.ReactNativeWebView;
      console.log('[Native] Android WebView bridge detected');
    } else {
      // Check for Capacitor/Cordova
      if (window.Capacitor) {
        this.nativeAPI = window.Capacitor;
        console.log('[Native] Capacitor bridge detected');
      }
    }
  }

  // iOS implementation
  initIOS() {
    if (window.webkit && window.webkit.messageHandlers) {
      this.nativeAPI = window.webkit.messageHandlers;
      console.log('[Native] iOS WKWebView bridge detected');
    }
  }

  // Windows implementation
  initWindows() {
    if (window.chrome && window.chrome.webview) {
      this.nativeAPI = window.chrome.webview;
      console.log('[Native] Windows WebView2 bridge detected');
    }
  }

  // Linux implementation
  initLinux() {
    // Check for Tauri bridge
    if (window.__TAURI__) {
      this.nativeAPI = window.__TAURI__;
      console.log('[Native] Tauri bridge detected (Linux)');
    }
  }

  // macOS implementation
  initMacOS() {
    if (window.__TAURI__) {
      this.nativeAPI = window.__TAURI__;
      console.log('[Native] Tauri bridge detected (macOS)');
    }
  }

  // Web fallback
  initWeb() {
    this.nativeAPI = null;
    console.log('[Native] Running in web mode (limited native features)');
  }

  // Floating window support
  async requestFloatingWindow() {
    try {
      switch (this.platform) {
        case 'android':
          return this.sendNativeMessage('requestOverlayPermission');
        case 'windows':
          return this.sendNativeMessage('createOverlayWindow');
        case 'linux':
          return this.sendNativeMessage('createGtkOverlay');
        default:
          console.warn(`[Native] Floating window not supported on ${this.platform}`);
          return false;
      }
    } catch (error) {
      console.error('[Native] Floating window error:', error);
      return false;
    }
  }

  // Screenshot capture
  async captureScreen() {
    try {
      if (this.platform === 'web') {
        // Web API fallback
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: { mediaSource: 'screen' }
        });
        return stream;
      }
      return this.sendNativeMessage('captureScreen');
    } catch (error) {
      console.error('[Native] Screenshot error:', error);
      return null;
    }
  }

  // Push notifications
  async requestNotificationPermission() {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      this.permissions.notifications = permission === 'granted';
      return this.permissions.notifications;
    }
    return false;
  }

  async showNotification(title, options = {}) {
    if (this.permissions.notifications || await this.requestNotificationPermission()) {
      new Notification(title, {
        body: options.body,
        icon: options.icon || '/favicon.ico',
        tag: options.tag,
        data: options.data,
      });
    }
  }

  // Biometric authentication
  async authenticateBiometric() {
    try {
      if (window.PublicKeyCredential) {
        // WebAuthn support
        const challenge = new Uint8Array(32);
        crypto.getRandomValues(challenge);
        
        const options = {
          publicKey: {
            challenge,
            rp: { name: 'AsimNexus' },
            user: { id: new Uint8Array(16), name: 'user', displayName: 'User' },
            pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
          }
        };
        
        const credential = await navigator.credentials.create(options);
        return !!credential;
      }
      return false;
    } catch (error) {
      console.error('[Native] Biometric error:', error);
      return false;
    }
  }

  // Send message to native layer
  sendNativeMessage(action, data = {}) {
    if (!this.nativeAPI) {
      console.warn('[Native] No native bridge available');
      return Promise.resolve(null);
    }
    
    const message = JSON.stringify({ action, data, timestamp: Date.now() });
    
    switch (this.platform) {
      case 'android':
        if (this.nativeAPI.postMessage) {
          this.nativeAPI.postMessage(message);
        }
        break;
      case 'ios':
        if (this.nativeAPI.asimBridge) {
          this.nativeAPI.asimBridge.postMessage(message);
        }
        break;
      case 'windows':
        if (this.nativeAPI.postMessage) {
          this.nativeAPI.postMessage(message);
        }
        break;
      case 'linux':
      case 'macos':
        if (this.nativeAPI.invoke) {
          return this.nativeAPI.invoke('asim_command', { action, data });
        }
        break;
    }
    
    return Promise.resolve({ status: 'sent', action });
  }

  // Get platform info
  getPlatformInfo() {
    return {
      platform: this.platform,
      userAgent: navigator.userAgent,
      screen: {
        width: window.screen.width,
        height: window.screen.height,
      },
      language: navigator.language,
      online: navigator.onLine,
    };
  }
}

const nativeBridge = new NativeBridge();
export { nativeBridge, PLATFORM };
export default nativeBridge;
