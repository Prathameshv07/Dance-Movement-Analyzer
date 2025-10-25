/**
 * WebSocket Client Manager
 * Handles real-time communication with server
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.heartbeatInterval = null;
        this.callbacks = {
            onOpen: null,
            onClose: null,
            onError: null,
            onMessage: null,
            onProgress: null,
            onComplete: null
        };
    }
    
    /**
     * Connect to WebSocket server
     */
    connect(sessionId) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
        
        console.log(`Connecting to WebSocket: ${wsUrl}`);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            
            if (this.callbacks.onOpen) {
                this.callbacks.onOpen(event);
            }
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket closed');
            this.stopHeartbeat();
            
            if (this.callbacks.onClose) {
                this.callbacks.onClose(event);
            }
            
            // Attempt reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                
                setTimeout(() => {
                    this.connect(sessionId);
                }, this.reconnectDelay);
            }
        };
    }
    
    /**
     * Handle incoming messages
     */
    handleMessage(message) {
        console.log('WebSocket message:', message);
        
        if (this.callbacks.onMessage) {
            this.callbacks.onMessage(message);
        }
        
        switch (message.type) {
            case 'connected':
                console.log('WebSocket connection confirmed');
                break;
                
            case 'progress':
                if (this.callbacks.onProgress) {
                    this.callbacks.onProgress(message.progress, message.message);
                }
                break;
                
            case 'status':
                console.log('Status update:', message.status, message.message);
                break;
                
            case 'complete':
                if (this.callbacks.onComplete) {
                    this.callbacks.onComplete(message);
                }
                this.close();
                break;
                
            case 'error':
                console.error('Server error:', message.message);
                if (this.callbacks.onError) {
                    this.callbacks.onError(new Error(message.message));
                }
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            case 'keepalive':
                // Server keepalive
                break;
        }
    }
    
    /**
     * Send message to server
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            if (typeof message === 'object') {
                this.ws.send(JSON.stringify(message));
            } else {
                this.ws.send(message);
            }
        } else {
            console.warn('WebSocket is not open. Cannot send message.');
        }
    }
    
    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send('ping');
        }, 20000); // Every 20 seconds
    }
    
    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    /**
     * Close WebSocket connection
     */
    close() {
        this.stopHeartbeat();
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    /**
     * Check if WebSocket is connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
    
    /**
     * Set callback handlers
     */
    on(event, callback) {
        if (this.callbacks.hasOwnProperty(`on${event.charAt(0).toUpperCase() + event.slice(1)}`)) {
            this.callbacks[`on${event.charAt(0).toUpperCase() + event.slice(1)}`] = callback;
        }
    }
}

// Export for use in main app
const wsClient = new WebSocketClient();