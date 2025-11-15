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
            eta: document.getElementById('etaTime'),
            status: document.getElementById('statusValue')
        };
        this.startTime = null;
        this.interval = null;
        this.lastProgress = 0;
    }
    
    start() {
        this.startTime = Date.now();
        this.lastProgress = 0;
        this.updateElapsedTime();
        
        // Update elapsed time every second
        this.interval = setInterval(() => {
            this.updateElapsedTime();
        }, 1000);
        
        console.log('⏱️ Progress tracking started');
    }
    
    update(progress, message = '') {
        const percentage = Math.round(progress * 100);
        
        console.log(`📊 Updating progress: ${percentage}% - ${message}`);
        
        if (this.elements.fill) {
            this.elements.fill.style.width = `${percentage}%`;
        }
        
        if (this.elements.text) {
            this.elements.text.textContent = `${percentage}%`;
        }
        
        if (this.elements.message && message) {
            this.elements.message.textContent = message;
        }
        
        if (this.elements.status) {
            this.elements.status.textContent = 'Processing';
        }
        
        // Update ETA
        this.lastProgress = progress;
        this.updateETA(progress);
    }
    
    updateElapsedTime() {
        if (!this.startTime || !this.elements.elapsed) return;
        
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        this.elements.elapsed.textContent = this.formatTime(elapsed);
    }
    
    updateETA(progress) {
        if (!this.startTime || !this.elements.eta || progress <= 0) {
            if (this.elements.eta) {
                this.elements.eta.textContent = 'Calculating...';
            }
            return;
        }
        
        // Calculate ETA based on current progress
        const elapsed = (Date.now() - this.startTime) / 1000; // seconds
        const estimatedTotal = elapsed / progress;
        const remaining = Math.max(0, estimatedTotal - elapsed);
        
        console.log(`⏱️ ETA: ${remaining.toFixed(0)}s remaining (${(progress * 100).toFixed(0)}% complete)`);
        
        if (this.elements.eta) {
            if (remaining > 0 && progress < 1.0) {
                this.elements.eta.textContent = this.formatTime(Math.ceil(remaining));
            } else {
                this.elements.eta.textContent = 'Almost done!';
            }
        }
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
        console.log('✅ Progress complete!');
        this.update(1.0, 'Analysis complete!');
        
        if (this.elements.status) {
            this.elements.status.textContent = 'Complete';
        }
        
        if (this.elements.eta) {
            this.elements.eta.textContent = 'Done!';
        }
        
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
        this.lastProgress = 0;
        
        if (this.elements.fill) this.elements.fill.style.width = '0%';
        if (this.elements.text) this.elements.text.textContent = '0%';
        if (this.elements.message) this.elements.message.textContent = '';
        if (this.elements.elapsed) this.elements.elapsed.textContent = '0s';
        if (this.elements.eta) this.elements.eta.textContent = '--';
        if (this.elements.status) this.elements.status.textContent = 'Ready';
        
        console.log('🔄 Progress reset');
    }
}

// Global progress manager
export const progressManager = new ProgressManager();