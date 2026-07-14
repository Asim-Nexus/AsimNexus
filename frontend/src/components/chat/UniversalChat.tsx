/**
 * UniversalChat.tsx
 * Full-page chat using OmniChat component
 * All features: Clones, Voice, Files, Smart suggestions, Context awareness
 */
import OmniChat from './OmniChat';

interface UniversalChatProps {
    user?: Record<string, unknown>;
    onCommand?: (cmd: string) => void;
}

export default function UniversalChat({ user, onCommand }: UniversalChatProps) {
    return (
        <div style={{ height: '100%', overflow: 'hidden' }}>
            <OmniChat
                user={user}
                onCommand={onCommand}
            />
        </div>
    );
}
