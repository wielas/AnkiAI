/**
 * Application configuration derived from environment variables.
 *
 * In development: Uses Vite proxy (empty string for API_URL)
 * In production: Uses VITE_API_URL environment variable
 */

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

/**
 * Derives WebSocket URL from API URL.
 * Handles protocol conversion: http->ws, https->wss
 */
function getWebSocketUrl() {
    if (!API_URL) {
        // Dev mode - use Vite proxy
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}`;
    }
    // Prod mode - derive from API_URL
    const url = new URL(API_URL);
    const wsProtocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${url.host}`;
}

export const config = {
    apiUrl: API_URL,
    wsUrl: getWebSocketUrl(),
};

export function apiEndpoint(path) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${config.apiUrl}${normalizedPath}`;
}

export function wsEndpoint(path) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${config.wsUrl}${normalizedPath}`;
}
