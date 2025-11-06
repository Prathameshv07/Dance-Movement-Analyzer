/**
 * Frontend Configuration
 */

export const APP_CONFIG = {
    API_BASE_URL: window.location.origin,
    WS_PROTOCOL: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
    
    // Polling configuration (for Celery)
    POLLING_INTERVAL: 2000, // 2 seconds
    MAX_POLL_ATTEMPTS: 300,  // 10 minutes max
    
    // File validation
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
    ALLOWED_EXTENSIONS: ['.mp4', '.webm', '.avi', '.mov'],
    ALLOWED_MIME_TYPES: ['video/mp4', 'video/webm', 'video/x-msvideo', 'video/quicktime'],
    
    // UI
    TOAST_DURATION: 3000,
    PROGRESS_UPDATE_THROTTLE: 500,
    
    // Features
    USE_WEBSOCKET: false,  // Set to true to use WebSocket instead of polling
    SHOW_ETA: true
};