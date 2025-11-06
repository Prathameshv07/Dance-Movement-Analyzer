/**
 * Progress Bar Manager
 */

export class ProgressManager {
    constructor() {
        this.elements = {
            fill: document.getElementById('progressFill'),
            text: document.getElementById('progressText'),
            message: document.getElementById('processingMessage'),
            elapsed: document.getElementById('elapsedTime'),
            eta: document.getElementById('etaTime')  // New element for ETA
        };
        this.startTime = null;
        this.interval = null;
    }
    
    start() {
        this.startTime = Date.now();
        this.updateElapsedTime();
        
        // Update elapsed time every second
        this.interval = setInterval(() => {
            this.updateElapsedTime();
        }, 1000);
    }
    
    update(progress, message = '') {
        const percentage = Math.round(progress * 100);
        
        if (this.elements.fill) {
            this.elements.fill.style.width = `${percentage}%`;
        }
        
        if (this.elements.text) {
            this.elements.text.textContent = `${percentage}%`;
        }
        
        if (this.elements.message && message) {
            this.elements.message.textContent = message;
        }
        
        // Update ETA
        this.updateETA(progress);
    }
    
    updateElapsedTime() {
        if (!this.startTime || !this.elements.elapsed) return;
        
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        this.elements.elapsed.textContent = this.formatTime(elapsed);
    }
    
    updateETA(progress) {
        if (!this.startTime || !this.elements.eta || progress <= 0) return;
        
        const elapsed = Date.now() - this.startTime;
        const estimatedTotal = elapsed / progress;
        const remaining = Math.max(0, estimatedTotal - elapsed);
        const etaSeconds = Math.ceil(remaining / 1000);
        
        this.elements.eta.textContent = this.formatTime(etaSeconds);
    }
    
    formatTime(seconds) {
        if (seconds < 60) {
            return `${seconds}s`;
        } else if (seconds < 3600) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}m ${secs}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${mins}m`;
        }
    }
    
    complete() {
        this.update(1.0, 'Analysis complete!');
        this.stop();
    }
    
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
    
    reset() {
        this.stop();
        this.startTime = null;
        
        if (this.elements.fill) this.elements.fill.style.width = '0%';
        if (this.elements.text) this.elements.text.textContent = '0%';
        if (this.elements.message) this.elements.message.textContent = '';
        if (this.elements.elapsed) this.elements.elapsed.textContent = '0s';
        if (this.elements.eta) this.elements.eta.textContent = '--';
    }
}

// Global progress manager
export const progressManager = new ProgressManager();