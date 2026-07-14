/**
 * NativeBridge Stub
 * ==================
 * Minimal stub for the native bridge module.
 * The full native/ directory was removed during consolidation;
 * this stub provides the exports needed by remaining components.
 */

export const PLATFORM = 'web';

export const nativeBridge = {
    init: () => {
        console.log('[NativeBridge] Running in web mode — native features unavailable');
    },
    captureScreen: async (): Promise<string | null> => {
        console.warn('[NativeBridge] captureScreen not available on web');
        return null;
    },
};
