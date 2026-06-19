/**
 * GestureService.js
 * Phase 4: Advanced gesture and input handling
 * Supports: mouse gestures, keyboard shortcuts, camera-based gestures
 */

class GestureService {
  constructor() {
    this.handlers = new Map();
    this.isTracking = false;
    this.gestureHistory = [];
    this.maxHistory = 50;
    this.gesturePatterns = new Map();
    this.registerDefaultPatterns();
  }

  registerDefaultPatterns() {
    // Swipe patterns for quick actions
    this.gesturePatterns.set('swipe-up', { action: 'expand_orb', description: 'Expand Asim Orb' });
    this.gesturePatterns.set('swipe-down', { action: 'collapse_orb', description: 'Collapse Asim Orb' });
    this.gesturePatterns.set('swipe-right', { action: 'next_tab', description: 'Next tab' });
    this.gesturePatterns.set('swipe-left', { action: 'prev_tab', description: 'Previous tab' });
    this.gesturePatterns.set('circle', { action: 'refresh', description: 'Refresh context' });
    this.gesturePatterns.set('double-tap', { action: 'quick_action', description: 'Quick action menu' });
  }

  init(element = document) {
    if (this.isTracking) return;
    this.isTracking = true;
    
    // Mouse gesture tracking
    this.setupMouseGestures(element);
    
    // Keyboard shortcuts
    this.setupKeyboardShortcuts();
    
    // Touch gestures (mobile)
    this.setupTouchGestures(element);
  }

  setupMouseGestures(element) {
    if (typeof document === 'undefined') return;
    
    let startX, startY, startTime;
    let isDragging = false;
    
    element.addEventListener('mousedown', (e) => {
      if (e.button === 2) { // Right-click
        this.emit('right_click', { x: e.clientX, y: e.clientY });
        return;
      }
      startX = e.clientX;
      startY = e.clientY;
      startTime = Date.now();
      isDragging = true;
    });
    
    element.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      this.emit('drag', { x: e.clientX, y: e.clientY, dx: e.clientX - startX, dy: e.clientY - startY });
    });
    
    element.addEventListener('mouseup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const dt = Date.now() - startTime;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < 10 && dt < 200) {
        this.emit('click', { x: e.clientX, y: e.clientY });
      } else if (distance > 50) {
        this.detectSwipe(dx, dy);
      }
    });
    
    // Scroll wheel
    element.addEventListener('wheel', (e) => {
      this.emit('scroll', { deltaX: e.deltaX, deltaY: e.deltaY });
    });
  }

  setupKeyboardShortcuts() {
    if (typeof document === 'undefined') return;
    
    document.addEventListener('keydown', (e) => {
      // Alt+A = Toggle Asim Orb
      if (e.altKey && e.key === 'a') {
        e.preventDefault();
        this.emit('shortcut', { action: 'toggle_orb' });
      }
      
      // Alt+S = Screenshot analysis
      if (e.altKey && e.key === 's') {
        e.preventDefault();
        this.emit('shortcut', { action: 'screenshot_analyze' });
      }
      
      // Alt+V = Voice mode
      if (e.altKey && e.key === 'v') {
        e.preventDefault();
        this.emit('shortcut', { action: 'voice_mode' });
      }
      
      // Alt+Z = Zen mode (focus)
      if (e.altKey && e.key === 'z') {
        e.preventDefault();
        this.emit('shortcut', { action: 'zen_mode' });
      }
      
      // Global shortcuts
      if (e.key === 'Escape') {
        this.emit('shortcut', { action: 'escape' });
      }
    });
  }

  setupTouchGestures(element) {
    if (typeof document === 'undefined') return;
    
    let touchStartX, touchStartY;
    
    element.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    
    element.addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - touchStartX;
      const dy = e.changedTouches[0].clientY - touchStartY;
      this.detectSwipe(dx, dy);
    }, { passive: true });
    
    element.addEventListener('touchmove', (e) => {
      // Prevent default only for horizontal swipes
      if (Math.abs(e.touches[0].clientX - touchStartX) > 10) {
        e.preventDefault();
      }
    }, { passive: false });
  }

  detectSwipe(dx, dy) {
    const minSwipe = 50;
    if (Math.abs(dx) < minSwipe && Math.abs(dy) < minSwipe) return;
    
    let gesture;
    if (Math.abs(dx) > Math.abs(dy)) {
      gesture = dx > 0 ? 'swipe-right' : 'swipe-left';
    } else {
      gesture = dy > 0 ? 'swipe-down' : 'swipe-up';
    }
    
    const pattern = this.gesturePatterns.get(gesture);
    if (pattern) {
      this.emit('gesture', { type: gesture, ...pattern });
    }
  }

  // Camera-based gesture (requires webcam permission)
  async initCameraGestures() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      this.videoStream = stream;
      // In a real implementation, this would use TensorFlow.js or MediaPipe
      // for hand tracking and gesture recognition
      console.log('[Gesture] Camera initialized for gesture recognition');
    } catch (error) {
      console.warn('[Gesture] Camera access denied:', error);
    }
  }

  on(event, callback) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event).push(callback);
    return () => {
      const callbacks = this.handlers.get(event);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) callbacks.splice(index, 1);
      }
    };
  }

  emit(event, data) {
    const callbacks = this.handlers.get(event);
    if (callbacks) {
      callbacks.forEach(cb => cb(data));
    }
    
    // Log gesture history
    this.gestureHistory.push({ event, data, timestamp: Date.now() });
    if (this.gestureHistory.length > this.maxHistory) {
      this.gestureHistory.shift();
    }
  }

  destroy() {
    this.isTracking = false;
    this.handlers.clear();
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
    }
  }
}

const gestureService = new GestureService();
export default gestureService;
