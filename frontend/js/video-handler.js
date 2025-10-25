/**
 * Video Handler
 * Utilities for video validation, preview, and synchronization
 */

class VideoHandler {
    constructor() {
        this.originalVideo = null;
        this.analyzedVideo = null;
        this.syncEnabled = false;
    }
    
    /**
     * Initialize video elements
     */
    init(originalId, analyzedId) {
        this.originalVideo = document.getElementById(originalId);
        this.analyzedVideo = document.getElementById(analyzedId);
        
        if (this.originalVideo && this.analyzedVideo) {
            this.setupSynchronization();
        }
    }
    
    /**
     * Setup playback synchronization between videos
     */
    setupSynchronization() {
        // Sync play/pause
        this.originalVideo.addEventListener('play', () => {
            if (this.syncEnabled && this.analyzedVideo.paused) {
                this.analyzedVideo.play();
            }
        });
        
        this.originalVideo.addEventListener('pause', () => {
            if (this.syncEnabled && !this.analyzedVideo.paused) {
                this.analyzedVideo.pause();
            }
        });
        
        // Sync seeking
        this.originalVideo.addEventListener('seeked', () => {
            if (this.syncEnabled) {
                this.analyzedVideo.currentTime = this.originalVideo.currentTime;
            }
        });
        
        // Enable sync by default
        this.syncEnabled = true;
    }
    
    /**
     * Toggle synchronization
     */
    toggleSync() {
        this.syncEnabled = !this.syncEnabled;
        return this.syncEnabled;
    }
    
    /**
     * Validate video file
     */
    validateFile(file) {
        const validTypes = ['video/mp4', 'video/webm', 'video/avi', 'video/mov'];
        const maxSize = 100 * 1024 * 1024; // 100MB
        
        if (!validTypes.includes(file.type)) {
            return {
                valid: false,
                error: 'Invalid file type. Please upload MP4, WebM, AVI, or MOV.'
            };
        }
        
        if (file.size > maxSize) {
            return {
                valid: false,
                error: 'File size exceeds 100MB limit.'
            };
        }
        
        return { valid: true };
    }
    
    /**
     * Get video metadata
     */
    async getMetadata(file) {
        return new Promise((resolve, reject) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            
            video.onloadedmetadata = () => {
                URL.revokeObjectURL(video.src);
                resolve({
                    duration: video.duration,
                    width: video.videoWidth,
                    height: video.videoHeight
                });
            };
            
            video.onerror = () => {
                reject(new Error('Failed to load video metadata'));
            };
            
            video.src = URL.createObjectURL(file);
        });
    }
    
    /**
     * Create thumbnail from video
     */
    async createThumbnail(videoElement, time = 1) {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            videoElement.currentTime = time;
            
            videoElement.addEventListener('seeked', function capture() {
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                
                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(URL.createObjectURL(blob));
                    } else {
                        reject(new Error('Failed to create thumbnail'));
                    }
                });
                
                videoElement.removeEventListener('seeked', capture);
            });
        });
    }
    
    /**
     * Format duration to MM:SS
     */
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Get video info string
     */
    getVideoInfo(metadata) {
        return `${metadata.width}x${metadata.height} • ${this.formatDuration(metadata.duration)}`;
    }
}

// Export for use in main app
const videoHandler = new VideoHandler();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    videoHandler.init('originalVideo', 'analyzedVideo');
});