/**
 * Toast Notification System
 */

import { APP_CONFIG } from '../core/config.js';

export class ToastManager {
    constructor(toastElement) {
        this.toastElement = toastElement || document.getElementById('toast');
    }
    
    show(message, type = 'info') {
        if (!this.toastElement) return;
        
        this.toastElement.textContent = message;
        this.toastElement.className = `toast ${type} show`;
        
        setTimeout(() => {
            this.toastElement.classList.remove('show');
        }, APP_CONFIG.TOAST_DURATION);
    }
    
    success(message) {
        this.show(message, 'success');
    }
    
    error(message) {
        this.show(message, 'error');
    }
    
    info(message) {
        this.show(message, 'info');
    }
    
    warning(message) {
        this.show(message, 'warning');
    }
}

// Global toast manager
export const toast = new ToastManager();