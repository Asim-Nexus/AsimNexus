/**
 * ASIMNEXUS Mobile Configuration
 * 
 * API_BASE_URL can be overridden via environment variable or config file.
 * Default: http://localhost:8000 (matches simple_backend.py)
 */

// Allow override via environment variable (for CI/CD or managed builds)
const ENV_API_URL = typeof process !== 'undefined' && process.env && process.env.ASIMNEXUS_API_URL;

// Default: port 8000 matches simple_backend.py
const DEFAULT_API_URL = 'http://localhost:8000';

export const API_BASE_URL = ENV_API_URL || DEFAULT_API_URL;

export default {
    API_BASE_URL,
    timeout: 10000,
};
