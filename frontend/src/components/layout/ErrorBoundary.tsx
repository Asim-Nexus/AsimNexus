/**
 * Error Boundary Component for ASIMNEXUS
 * Catches React errors and prevents app crashes
 */
import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

// Extend Window for gtag
declare global {
    interface Window {
        gtag?: (event: string, action: string, params: Record<string, unknown>) => void;
    }
}

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
    errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
        console.error('ErrorBoundary caught error:', error, errorInfo);
        this.setState({ errorInfo });

        // Log to monitoring service
        if (window.gtag) {
            window.gtag('event', 'error', {
                event_category: 'react_error',
                event_label: error.message,
                value: 1,
            });
        }
    }

    handleReload = (): void => {
        window.location.reload();
    };

    handleGoHome = (): void => {
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary-container">
                    <div className="error-boundary-content">
                        <div className="error-icon">
                            <AlertCircle size={64} />
                        </div>
                        <h1>Something Went Wrong</h1>
                        <p className="error-message">
                            AsimNexus encountered an unexpected error. Our self-healing system has been notified.
                        </p>
                        {this.state.error && (
                            <div className="error-details">
                                <code>{this.state.error.message}</code>
                            </div>
                        )}
                        <div className="error-actions">
                            <button onClick={this.handleReload} className="error-btn primary">
                                <RefreshCw size={18} />
                                Reload Application
                            </button>
                            <button onClick={this.handleGoHome} className="error-btn secondary">
                                <Home size={18} />
                                Go to Home
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
