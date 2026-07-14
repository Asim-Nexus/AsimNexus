/**
 * UniversalChatSimple.tsx
 * Full-page chat using UnifiedChat component
 * All features: Clones, Voice, Files, Smart suggestions, Context awareness
 */
import UnifiedChat from '../shared/UnifiedChat';

interface UniversalChatSimpleProps {
    user?: Record<string, unknown>;
    onCommand?: (cmd: string) => void;
}

export default function UniversalChatSimple({ user, onCommand }: UniversalChatSimpleProps) {
    return (
        <div style={{ height: '100%' }}>
            <UnifiedChat
                user={user}
                onCommand={onCommand}
                compact={false}  // Full page mode
            />
        </div>
    );
}
