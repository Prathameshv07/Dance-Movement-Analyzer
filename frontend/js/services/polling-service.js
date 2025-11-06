/**
 * Task Polling Service (replaces WebSocket for Celery)
 */

import { APP_CONFIG } from '../core/config.js';
import { apiService } from './api-service.js';

export class PollingService {
    constructor() {
        this.pollInterval = null;
        this.onProgress = null;
        this.onComplete = null;
        this.onError = null;
        this.pollCount = 0;
    }
    
    startPolling(taskId, callbacks = {}) {
        this.onProgress = callbacks.onProgress || (() => {});
        this.onComplete = callbacks.onComplete || (() => {});
        this.onError = callbacks.onError || (() => {});
        this.pollCount = 0;
        
        console.log(`Starting polling for task: ${taskId}`);
        
        this.pollInterval = setInterval(async () => {
            try {
                this.pollCount++;
                
                // Max poll attempts check
                if (this.pollCount > APP_CONFIG.MAX_POLL_ATTEMPTS) {
                    this.stopPolling();
                    this.onError(new Error('Polling timeout'));
                    return;
                }
                
                const status = await apiService.getTaskStatus(taskId);
                
                if (status.state === 'PROGRESS' || status.state === 'PENDING') {
                    this.onProgress(status.progress || 0, status.message || 'Processing...');
                } else if (status.state === 'SUCCESS') {
                    this.stopPolling();
                    this.onComplete(status.result);
                } else if (status.state === 'FAILURE') {
                    this.stopPolling();
                    this.onError(new Error(status.error || 'Task failed'));
                }
                
            } catch (error) {
                console.error('Polling error:', error);
                // Don't stop on single error, retry
            }
        }, APP_CONFIG.POLLING_INTERVAL);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('Polling stopped');
        }
    }
}

// Global polling service instance
export const pollingService = new PollingService();