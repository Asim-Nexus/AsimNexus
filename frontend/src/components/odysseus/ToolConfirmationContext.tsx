/**
 * ToolConfirmationContext.tsx
 * Global context for ToolConfirmationDialog, allowing any component
 * to trigger the approve/reject dialog for a pending tool execution.
 */
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface ToolConfirmationContextValue {
    dialogOpen: boolean;
    pendingExecution: Record<string, unknown> | null;
    openDialog: (execution: Record<string, unknown>) => void;
    closeDialog: () => void;
}

const ToolConfirmationCtx = createContext<ToolConfirmationContextValue | null>(null);

interface ToolConfirmationProviderProps {
    children: ReactNode;
}

export function ToolConfirmationProvider({ children }: ToolConfirmationProviderProps) {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [pendingExecution, setPendingExecution] = useState<Record<string, unknown> | null>(null);

    const openDialog = useCallback((execution: Record<string, unknown>) => {
        setPendingExecution(execution);
        setDialogOpen(true);
    }, []);

    const closeDialog = useCallback(() => {
        setDialogOpen(false);
        setPendingExecution(null);
    }, []);

    const value: ToolConfirmationContextValue = {
        dialogOpen,
        pendingExecution,
        openDialog,
        closeDialog,
    };

    return (
        <ToolConfirmationCtx.Provider value={value}>
            {children}
        </ToolConfirmationCtx.Provider>
    );
}

export function useToolConfirmation(): ToolConfirmationContextValue {
    const ctx = useContext(ToolConfirmationCtx);
    if (!ctx) {
        throw new Error('useToolConfirmation must be used within a ToolConfirmationProvider');
    }
    return ctx;
}

export default ToolConfirmationCtx;
