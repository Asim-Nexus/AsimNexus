import { useState, useEffect } from 'react';

interface ColorPalette {
    primary: string;
    secondary: string;
    background: string;
    text: string;
}

interface UseAIPersonalizationReturn {
    theme: string;
    accentColor: string;
    layoutMode: string;
    userMood: string;
    setTheme: React.Dispatch<React.SetStateAction<string>>;
    setAccentColor: React.Dispatch<React.SetStateAction<string>>;
    setLayoutMode: React.Dispatch<React.SetStateAction<string>>;
    setUserMood: React.Dispatch<React.SetStateAction<string>>;
    getColorPalette: () => ColorPalette;
}

const useAIPersonalization = (): UseAIPersonalizationReturn => {
    const [theme, setTheme] = useState<string>('dark');
    const [accentColor, setAccentColor] = useState<string>('#667eea');
    const [layoutMode, setLayoutMode] = useState<string>('default');
    const [userMood, setUserMood] = useState<string>('focused');

    // Detect time of day for adaptive theming
    useEffect(() => {
        const hour = new Date().getHours();
        const isNight = hour >= 20 || hour < 6;
        const isMorning = hour >= 6 && hour < 12;
        const isAfternoon = hour >= 12 && hour < 17;

        if (isNight) {
            setTheme('dark');
            setAccentColor('#667eea'); // Purple for night
        } else if (isMorning) {
            setTheme('light');
            setAccentColor('#10b981'); // Green for morning energy
        } else if (isAfternoon) {
            setTheme('light');
            setAccentColor('#3b82f6'); // Blue for afternoon focus
        } else {
            setTheme('dark');
            setAccentColor('#f59e0b'); // Orange for evening warmth
        }
    }, []);

    // Detect user activity for mood-based personalization
    useEffect(() => {
        let activityTimeout: ReturnType<typeof setInterval>;
        let lastActivity = Date.now();

        const handleActivity = () => {
            lastActivity = Date.now();
            setUserMood('active');
        };

        const checkInactivity = () => {
            const inactiveTime = Date.now() - lastActivity;
            if (inactiveTime > 300000) { // 5 minutes inactive
                setUserMood('calm');
            } else if (inactiveTime > 60000) { // 1 minute inactive
                setUserMood('focused');
            }
        };

        window.addEventListener('mousemove', handleActivity);
        window.addEventListener('keydown', handleActivity);
        window.addEventListener('click', handleActivity);

        activityTimeout = setInterval(checkInactivity, 10000);

        return () => {
            window.removeEventListener('mousemove', handleActivity);
            window.removeEventListener('keydown', handleActivity);
            window.removeEventListener('click', handleActivity);
            clearInterval(activityTimeout);
        };
    }, []);

    // Adaptive layout based on screen size and user preference
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setLayoutMode('mobile');
            } else if (window.innerWidth < 1024) {
                setLayoutMode('tablet');
            } else {
                setLayoutMode('desktop');
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Get adaptive color palette based on mood and time
    const getColorPalette = (): ColorPalette => {
        const palettes: Record<string, ColorPalette> = {
            focused: {
                primary: '#667eea',
                secondary: '#764ba2',
                background: 'rgba(15, 15, 26, 0.95)',
                text: '#ffffff',
            },
            calm: {
                primary: '#10b981',
                secondary: '#059669',
                background: 'rgba(15, 15, 26, 0.9)',
                text: '#e5e7eb',
            },
            active: {
                primary: '#f59e0b',
                secondary: '#d97706',
                background: 'rgba(15, 15, 26, 0.95)',
                text: '#ffffff',
            },
        };

        return palettes[userMood] || palettes.focused;
    };

    // Apply custom CSS variables for theming
    useEffect(() => {
        const palette = getColorPalette();
        const root = document.documentElement;

        root.style.setProperty('--accent-primary', palette.primary);
        root.style.setProperty('--accent-secondary', palette.secondary);
        root.style.setProperty('--theme-background', palette.background);
        root.style.setProperty('--theme-text', palette.text);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userMood, theme]);

    return {
        theme,
        accentColor,
        layoutMode,
        userMood,
        setTheme,
        setAccentColor,
        setLayoutMode,
        setUserMood,
        getColorPalette,
    };
};

export default useAIPersonalization;
