/**
 * GestureService.ts
 * Phase 4: Advanced gesture and input handling
 * Supports: mouse gestures, keyboard shortcuts, camera-based gestures
 */

interface GesturePattern {
    action: string;
    description: string;
}

interface GestureEvent {
    type: string;
    action: string;
    description: string;
}

interface DragData {
    x: number;
    y: number;
    dx: number;
    dy: number;
}

interface ClickData {
    x: number;
    y: number;
}

interface ScrollData {
    deltaX: number;
    deltaY: number;
}

interface ShortcutData {
    action: string;
}

interface GestureHistoryEntry {
    event: string;
    data: unknown;
    timestamp: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GestureCallback = (data: any) => void;

class GestureService {
    private handlers: Map<string, GestureCallback[]> = new Map();
    private isTracking: boolean = false;
    private gestureHistory: GestureHistoryEntry[] = [];
    private readonly maxHistory: number = 50;
    private gesturePatterns: Map<string, GesturePattern> = new Map();
    private videoStream: MediaStream | null = null;

    constructor() {
        this.registerDefaultPatterns();
    }

    private registerDefaultPatterns(): void {
        // Swipe patterns for quick actions
        this.gesturePatterns.set('swipe-up', { action: 'expand_orb', description: 'Expand Asim Orb' });
        this.gesturePatterns.set('swipe-down', { action: 'collapse_orb', description: 'Collapse Asim Orb' });
        this.gesturePatterns.set('swipe-right', { action: 'next_tab', description: 'Next tab' });
        this.gesturePatterns.set('swipe-left', { action: 'prev_tab', description: 'Previous tab' });
        this.gesturePatterns.set('circle', { action: 'refresh', description: 'Refresh context' });
        this.gesturePatterns.set('double-tap', { action: 'quick_action', description: 'Quick action menu' });
    }

    init(element: HTMLElement | Document = document): void {
        if (this.isTracking) return;
        this.isTracking = true;

        // Mouse gesture tracking
        this.setupMouseGestures(element);

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Touch gestures (mobile)
        this.setupTouchGestures(element);
    }

    private setupMouseGestures(element: HTMLElement | Document): void {
        if (typeof document === 'undefined') return;

        let startX = 0, startY = 0, startTime = 0;
        let isDragging = false;

        element.addEventListener('mousedown', (e: Event) => {
            const mouseEvent = e as MouseEvent;
            if (mouseEvent.button === 2) { // Right-click
                this.emit('right_click', { x: mouseEvent.clientX, y: mouseEvent.clientY });
                return;
            }
            startX = mouseEvent.clientX;
            startY = mouseEvent.clientY;
            startTime = Date.now();
            isDragging = true;
        });

        element.addEventListener('mousemove', (e: Event) => {
            if (!isDragging) return;
            const mouseEvent = e as MouseEvent;
            this.emit('drag', { x: mouseEvent.clientX, y: mouseEvent.clientY, dx: mouseEvent.clientX - startX, dy: mouseEvent.clientY - startY } as DragData);
        });

        element.addEventListener('mouseup', (e: Event) => {
            if (!isDragging) return;
            isDragging = false;

            const mouseEvent = e as MouseEvent;
            const dx = mouseEvent.clientX - startX;
            const dy = mouseEvent.clientY - startY;
            const dt = Date.now() - startTime;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 10 && dt < 200) {
                this.emit('click', { x: mouseEvent.clientX, y: mouseEvent.clientY } as ClickData);
            } else if (distance > 50) {
                this.detectSwipe(dx, dy);
            }
        });

        // Scroll wheel
        element.addEventListener('wheel', (e: Event) => {
            const wheelEvent = e as WheelEvent;
            this.emit('scroll', { deltaX: wheelEvent.deltaX, deltaY: wheelEvent.deltaY } as ScrollData);
        });
    }

    private setupKeyboardShortcuts(): void {
        if (typeof document === 'undefined') return;

        document.addEventListener('keydown', (e: KeyboardEvent) => {
            // Alt+A = Toggle Asim Orb
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                this.emit('shortcut', { action: 'toggle_orb' } as ShortcutData);
            }

            // Alt+S = Screenshot analysis
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.emit('shortcut', { action: 'screenshot_analyze' } as ShortcutData);
            }

            // Alt+V = Voice mode
            if (e.altKey && e.key === 'v') {
                e.preventDefault();
                this.emit('shortcut', { action: 'voice_mode' } as ShortcutData);
            }

            // Alt+Z = Zen mode (focus)
            if (e.altKey && e.key === 'z') {
                e.preventDefault();
                this.emit('shortcut', { action: 'zen_mode' } as ShortcutData);
            }

            // Global shortcuts
            if (e.key === 'Escape') {
                this.emit('shortcut', { action: 'escape' } as ShortcutData);
            }
        });
    }

    private setupTouchGestures(element: HTMLElement | Document): void {
        if (typeof document === 'undefined') return;

        let touchStartX = 0, touchStartY = 0;

        element.addEventListener('touchstart', (e: Event) => {
            const touchEvent = e as TouchEvent;
            touchStartX = touchEvent.touches[0].clientX;
            touchStartY = touchEvent.touches[0].clientY;
        }, { passive: true } as AddEventListenerOptions);

        element.addEventListener('touchend', (e: Event) => {
            const touchEvent = e as TouchEvent;
            const dx = touchEvent.changedTouches[0].clientX - touchStartX;
            const dy = touchEvent.changedTouches[0].clientY - touchStartY;
            this.detectSwipe(dx, dy);
        }, { passive: true } as AddEventListenerOptions);

        element.addEventListener('touchmove', (e: Event) => {
            const touchEvent = e as TouchEvent;
            // Prevent default only for horizontal swipes
            if (Math.abs(touchEvent.touches[0].clientX - touchStartX) > 10) {
                touchEvent.preventDefault();
            }
        }, { passive: false });
    }

    private detectSwipe(dx: number, dy: number): void {
        const minSwipe = 50;
        if (Math.abs(dx) < minSwipe && Math.abs(dy) < minSwipe) return;

        let gesture: string;
        if (Math.abs(dx) > Math.abs(dy)) {
            gesture = dx > 0 ? 'swipe-right' : 'swipe-left';
        } else {
            gesture = dy > 0 ? 'swipe-down' : 'swipe-up';
        }

        const pattern = this.gesturePatterns.get(gesture);
        if (pattern) {
            this.emit('gesture', { type: gesture, ...pattern } as GestureEvent);
        }
    }

    // Camera-based gesture (requires webcam permission)
    async initCameraGestures(): Promise<void> {
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

    on(event: string, callback: GestureCallback): () => void {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, []);
        }
        this.handlers.get(event)!.push(callback);
        return () => {
            const callbacks = this.handlers.get(event);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index > -1) callbacks.splice(index, 1);
            }
        };
    }

    private emit(event: string, data: unknown): void {
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

    destroy(): void {
        this.isTracking = false;
        this.handlers.clear();
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
    }
}

const gestureService = new GestureService();
export default gestureService;
