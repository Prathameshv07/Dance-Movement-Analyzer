/**
 * API Communication Service
 */

import { APP_CONFIG } from '../core/config.js';

export class APIService {
    constructor(baseURL = APP_CONFIG.API_BASE_URL) {
        this.baseURL = baseURL;
    }
    
    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseURL}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return await response.json();
    }
    
    async startAnalysis(sessionId) {
        const response = await fetch(`${this.baseURL}/api/analyze/${sessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed to start');
        }
        
        return await response.json();
    }
    
    // async getTaskStatus(taskId) {
    //     const response = await fetch(`${this.baseURL}/api/task/${taskId}`);
        
    //     if (!response.ok) {
    //         throw new Error('Failed to get task status');
    //     }
        
    //     return await response.json();
    // }
    
    async getResults(sessionId) {
        const response = await fetch(`${this.baseURL}/api/results/${sessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to get results');
        }
        
        return await response.json();
    }
    
    getDownloadURL(sessionId) {
        return `${this.baseURL}/api/download/${sessionId}`;
    }
    
    async getStorageStats() {
        const response = await fetch(`${this.baseURL}/api/admin/storage`);
        return await response.json();
    }
}

// Global API service instance
export const apiService = new APIService();