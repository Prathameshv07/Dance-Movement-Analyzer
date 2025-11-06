/**
 * Application State Management
 */

export class AppState {
    constructor() {
        this.sessionId = null;
        this.uploadedFile = null;
        this.videoInfo = null;
        this.results = null;
        this.taskId = null;
        this.pollingInterval = null;
        this.startTime = null;
        this.eta = null;
    }
    
    reset() {
        this.sessionId = null;
        this.uploadedFile = null;
        this.videoInfo = null;
        this.results = null;
        this.taskId = null;
        this.startTime = null;
        this.eta = null;
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    setSession(sessionId, fileInfo) {
        this.sessionId = sessionId;
        this.videoInfo = fileInfo;
    }
    
    setTask(taskId) {
        this.taskId = taskId;
        this.startTime = Date.now();
    }
    
    updateETA(progress) {
        if (!this.startTime || progress <= 0) return null;
        
        const elapsed = Date.now() - this.startTime;
        const estimatedTotal = elapsed / progress;
        const remaining = estimatedTotal - elapsed;
        
        this.eta = Math.max(0, Math.ceil(remaining / 1000)); // seconds
        return this.eta;
    }
}

// Global state instance
export const appState = new AppState();