/**
 * ToolConfirmationContext.jsx
 * Global context for ToolConfirmationDialog, allowing any component
 * to trigger the approve/reject dialog for a pending tool execution.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

const ToolConfirmationCtx = createContext(null);

export function ToolConfirmationProvider({ children }) {
    const [dialogOpen, setDialogOpen] = useState(false);
    const [pendingExecution, setPendingExecution] = useState(null);

    const openDialog = useCallback((execution) => {
        setPendingExecution(execution);
        setDialogOpen(true);
    }, []);

    const closeDialog = useCallback(() => {
        setDialogOpen(false);
        setPendingExecution(null);
    }, []);

    const value = {
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

export function useToolConfirmation() {
    const ctx = useContext(ToolConfirmationCtx);
    if (!ctx) {
        throw new Error('useToolConfirmation must be used within a ToolConfirmationProvider');
    }
    return ctx;
}

export default ToolConfirmationCtx;
