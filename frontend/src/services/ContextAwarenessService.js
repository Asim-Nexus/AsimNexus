/**
 * ContextAwarenessService.js
 * Phase 2: Smart Context Awareness for AsimOrb
 * Screen capture, OCR, and intelligent suggestions
 */

class ContextAwarenessService {
  constructor() {
    this.isActive = false;
    this.currentContext = null;
    this.screenshotCanvas = null;
    this.observers = [];
  }

  // Initialize context tracking
  init() {
    this.isActive = true;
    this.startContextTracking();
    console.log('[ContextAwareness] Service initialized');
  }

  // Start tracking active context
  startContextTracking() {
    // Track URL changes
    this.trackURLChanges();
    
    // Track active element
    this.trackFocusChanges();
    
    // Periodic context analysis
    this.analysisInterval = setInterval(() => {
      this.analyzeCurrentContext();
    }, 3000);
  }

  // Track URL/page changes
  trackURLChanges() {
    try {
      if (typeof document === 'undefined' || !document.body) return;
      let lastUrl = typeof window !== 'undefined' ? window.location?.href : '';
      
      this.urlObserver = new MutationObserver(() => {
        const url = typeof window !== 'undefined' ? window.location?.href : '';
        if (url !== lastUrl) {
          lastUrl = url;
          this.handlePageChange(url);
        }
      });
      
      this.urlObserver.observe(document.body, { subtree: true, childList: true });
    } catch (e) {
      console.warn('[ContextAwareness] URL tracking failed:', e);
    }
  }

  // Track focus changes
  trackFocusChanges() {
    if (typeof document === 'undefined') return;
    document.addEventListener('focusin', (e) => {
      this.currentContext = {
        ...this.currentContext,
        activeElement: e.target.tagName,
        inputType: e.target.type || 'text',
        placeholder: e.target.placeholder || '',
      };
    });
  }

  // Handle page navigation
  handlePageChange(url) {
    const context = this.extractContextFromURL(url);
    this.currentContext = { ...this.currentContext, ...context };
    this.notifyObservers('pageChange', context);
  }

  // Extract context from URL
  extractContextFromURL(url) {
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      const pathname = urlObj.pathname;
      
      // Detect app type
      let appType = 'general';
      let appName = 'Unknown';
      
      if (hostname.includes('github')) {
        appType = 'code';
        appName = 'GitHub';
      } else if (hostname.includes('youtube') || hostname.includes('vimeo')) {
        appType = 'video';
        appName = 'Video Player';
      } else if (hostname.includes('docs.google') || hostname.includes('office')) {
        appType = 'document';
        appName = 'Document Editor';
      } else if (hostname.includes('gmail') || hostname.includes('mail')) {
        appType = 'email';
        appName = 'Email Client';
      } else if (hostname.includes('chat') || hostname.includes('slack') || hostname.includes('discord')) {
        appType = 'chat';
        appName = 'Chat App';
      } else if (hostname.includes('twitter') || hostname.includes('facebook') || hostname.includes('instagram')) {
        appType = 'social';
        appName = 'Social Media';
      } else if (hostname.includes('amazon') || hostname.includes('ebay') || hostname.includes('shop')) {
        appType = 'shopping';
        appName = 'E-Commerce';
      } else if (hostname.includes('bank') || hostname.includes('paypal') || hostname.includes('finance')) {
        appType = 'banking';
        appName = 'Financial App';
      }
      
      return {
        url,
        hostname,
        pathname,
        appType,
        appName,
        timestamp: Date.now(),
      };
    } catch (e) {
      return { url, appType: 'unknown', appName: 'Unknown' };
    }
  }

  // Analyze current page content
  analyzeCurrentContext() {
    if (!this.isActive) return;
    
    const analysis = {
      timestamp: Date.now(),
      url: typeof window !== 'undefined' ? window.location?.href : '',
      title: typeof document !== 'undefined' ? document.title : '',
      hasImages: typeof document !== 'undefined' ? document.images.length : 0,
      hasVideos: typeof document !== 'undefined' ? document.querySelectorAll('video').length : 0,
      textContent: typeof document !== 'undefined' ? document.body?.innerText?.substring(0, 500) || '' : '',
    };
    
    this.currentContext = { ...this.currentContext, ...analysis };
  }

  // Capture screenshot (simulated - real implementation needs permissions)
  async captureScreenshot() {
    return {
      type: 'screenshot',
      timestamp: Date.now(),
      url: typeof window !== 'undefined' ? window.location?.href : '',
      simulated: true,
    };
  }

  // OCR simulation (real would use Tesseract.js or cloud OCR)
  async performOCR(imageData) {
    if (typeof document === 'undefined') return { text: '', blocks: [], confidence: 0 };
    const textElements = Array.from(document.querySelectorAll('p, h1, h2, h3, span, div'))
      .filter(el => el.innerText && el.innerText.length > 10)
      .slice(0, 10)
      .map(el => ({
        text: el.innerText.substring(0, 200),
        tag: el.tagName,
        rect: el.getBoundingClientRect(),
      }));
    
    return {
      text: textElements.map(t => t.text).join('\n'),
      blocks: textElements,
      confidence: 0.95,
    };
  }

  // Get smart suggestions based on context
  getSmartSuggestions() {
    const context = this.currentContext;
    if (!context) return [];
    
    const suggestions = [];
    
    switch (context.appType) {
      case 'code':
        suggestions.push(
          { icon: '💻', text: 'Explain this code', action: 'explain_code' },
          { icon: '🔍', text: 'Find bugs', action: 'find_bugs' },
          { icon: '📝', text: 'Generate README', action: 'gen_readme' },
          { icon: '🧪', text: 'Write tests', action: 'write_tests' }
        );
        break;
        
      case 'video':
        suggestions.push(
          { icon: '📜', text: 'Transcribe video', action: 'transcribe' },
          { icon: '🎯', text: 'Key moments', action: 'key_moments' },
          { icon: '📝', text: 'Summarize', action: 'summarize_video' },
          { icon: '💬', text: 'Generate captions', action: 'captions' }
        );
        break;
        
      case 'document':
        suggestions.push(
          { icon: '📄', text: 'Summarize doc', action: 'summarize_doc' },
          { icon: '✏️', text: 'Improve writing', action: 'improve_text' },
          { icon: '🔄', text: 'Translate', action: 'translate' },
          { icon: '📊', text: 'Extract data', action: 'extract_data' }
        );
        break;
        
      case 'email':
        suggestions.push(
          { icon: '✉️', text: 'Draft reply', action: 'draft_reply' },
          { icon: '📋', text: 'Summarize thread', action: 'summarize_thread' },
          { icon: '🏷️', text: 'Suggest labels', action: 'suggest_labels' },
          { icon: '⚡', text: 'Quick response', action: 'quick_reply' }
        );
        break;
        
      case 'chat':
        suggestions.push(
          { icon: '💬', text: 'Summarize chat', action: 'summarize_chat' },
          { icon: '📅', text: 'Extract tasks', action: 'extract_tasks' },
          { icon: '🎭', text: 'Suggest reply', action: 'suggest_reply' },
          { icon: '⏰', text: 'Set reminder', action: 'set_reminder' }
        );
        break;
        
      case 'shopping':
        suggestions.push(
          { icon: '🔍', text: 'Compare prices', action: 'compare_prices' },
          { icon: '⭐', text: 'Find reviews', action: 'find_reviews' },
          { icon: '💰', text: 'Check deals', action: 'check_deals' },
          { icon: '📦', text: 'Track order', action: 'track_order' }
        );
        break;
        
      case 'banking':
        suggestions.push(
          { icon: '📊', text: 'Analyze spending', action: 'analyze_spending' },
          { icon: '💡', text: 'Saving tips', action: 'saving_tips' },
          { icon: '📈', text: 'Investment advice', action: 'investment' },
          { icon: '🔒', text: 'Security check', action: 'security_check' }
        );
        break;
        
      default:
        suggestions.push(
          { icon: '📄', text: 'Page summary', action: 'summarize' },
          { icon: '💾', text: 'Save content', action: 'save' },
          { icon: '🔗', text: 'Share link', action: 'share' },
          { icon: '🔍', text: 'Search related', action: 'search' }
        );
    }
    
    return suggestions;
  }

  // Subscribe to context changes
  subscribe(callback) {
    this.observers.push(callback);
    return () => {
      this.observers = this.observers.filter(cb => cb !== callback);
    };
  }

  // Notify all observers
  notifyObservers(event, data) {
    this.observers.forEach(cb => cb(event, data));
  }

  // Get current context
  getCurrentContext() {
    return this.currentContext;
  }

  // Destroy service
  destroy() {
    this.isActive = false;
    clearInterval(this.analysisInterval);
    if (this.urlObserver) {
      try { this.urlObserver.disconnect(); } catch {}
    }
    this.observers = [];
  }
}

// Singleton instance
const contextService = new ContextAwarenessService();
export default contextService;