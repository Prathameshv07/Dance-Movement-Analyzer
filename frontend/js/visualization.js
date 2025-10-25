/**
 * Visualization Module
 * Handles canvas rendering, skeleton overlay, and visual effects
 */

class Visualizer {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.animationFrame = null;
        this.isPlaying = false;
        
        // Visualization settings
        this.settings = {
            showSkeleton: true,
            showKeypoints: true,
            showTrails: false,
            lineThickness: 2,
            pointRadius: 4,
            trailLength: 10
        };
        
        // Color scheme
        this.colors = {
            highConfidence: '#10b981',  // Green
            medConfidence: '#f59e0b',   // Orange
            lowConfidence: '#ef4444',   // Red
            connection: '#6366f1'       // Blue
        };
        
        // Trail history
        this.trailHistory = [];
        this.maxTrailLength = 30;
        
        // Skeleton connections (MediaPipe Pose landmark indices)
        this.connections = [
            // Face
            [0, 1], [1, 2], [2, 3], [3, 7],
            [0, 4], [4, 5], [5, 6], [6, 8],
            
            // Torso
            [9, 10], [11, 12], [11, 23], [12, 24], [23, 24],
            
            // Arms
            [11, 13], [13, 15], [15, 17], [15, 19], [15, 21],
            [12, 14], [14, 16], [16, 18], [16, 20], [16, 22],
            
            // Legs
            [23, 25], [25, 27], [27, 29], [27, 31],
            [24, 26], [26, 28], [28, 30], [28, 32]
        ];
    }
    
    /**
     * Initialize canvas overlay
     */
    init(videoId, canvasId = null) {
        const video = document.getElementById(videoId);
        if (!video) {
            console.error('Video element not found');
            return false;
        }
        
        // Create or get canvas
        if (canvasId) {
            this.canvas = document.getElementById(canvasId);
        } else {
            this.canvas = this.createOverlayCanvas(video);
        }
        
        if (!this.canvas) {
            console.error('Canvas element not found or could not be created');
            return false;
        }
        
        this.ctx = this.canvas.getContext('2d');
        
        // Match canvas size to video
        this.resizeCanvas(video);
        
        // Handle video resize
        video.addEventListener('loadedmetadata', () => {
            this.resizeCanvas(video);
        });
        
        window.addEventListener('resize', () => {
            this.resizeCanvas(video);
        });
        
        return true;
    }
    
    /**
     * Create overlay canvas above video
     */
    createOverlayCanvas(video) {
        const canvas = document.createElement('canvas');
        canvas.id = 'overlay-canvas';
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '10';
        
        // Insert canvas after video
        video.parentNode.style.position = 'relative';
        video.parentNode.appendChild(canvas);
        
        return canvas;
    }
    
    /**
     * Resize canvas to match video
     */
    resizeCanvas(video) {
        if (!this.canvas) return;
        
        this.canvas.width = video.videoWidth || video.clientWidth;
        this.canvas.height = video.videoHeight || video.clientHeight;
        this.canvas.style.width = video.clientWidth + 'px';
        this.canvas.style.height = video.clientHeight + 'px';
    }
    
    /**
     * Draw skeleton from pose landmarks
     */
    drawSkeleton(landmarks, confidence = 0.5) {
        if (!this.ctx || !landmarks || landmarks.length === 0) return;
        
        this.clear();
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Draw connections
        if (this.settings.showSkeleton) {
            this.ctx.lineWidth = this.settings.lineThickness;
            
            this.connections.forEach(([startIdx, endIdx]) => {
                if (startIdx < landmarks.length && endIdx < landmarks.length) {
                    const start = landmarks[startIdx];
                    const end = landmarks[endIdx];
                    
                    // Check visibility
                    if (start[2] > confidence && end[2] > confidence) {
                        const x1 = start[0] * width;
                        const y1 = start[1] * height;
                        const x2 = end[0] * width;
                        const y2 = end[1] * height;
                        
                        // Color based on average confidence
                        const avgConf = (start[2] + end[2]) / 2;
                        this.ctx.strokeStyle = this.getConfidenceColor(avgConf);
                        
                        // Draw line
                        this.ctx.beginPath();
                        this.ctx.moveTo(x1, y1);
                        this.ctx.lineTo(x2, y2);
                        this.ctx.stroke();
                    }
                }
            });
        }
        
        // Draw keypoints
        if (this.settings.showKeypoints) {
            landmarks.forEach((landmark, idx) => {
                if (landmark[2] > confidence) {
                    const x = landmark[0] * width;
                    const y = landmark[1] * height;
                    const conf = landmark[2];
                    
                    // Draw point
                    this.ctx.fillStyle = this.getConfidenceColor(conf);
                    this.ctx.beginPath();
                    this.ctx.arc(x, y, this.settings.pointRadius, 0, 2 * Math.PI);
                    this.ctx.fill();
                    
                    // Draw landmark index (for debugging)
                    // this.ctx.fillStyle = 'white';
                    // this.ctx.font = '10px Arial';
                    // this.ctx.fillText(idx, x + 5, y - 5);
                }
            });
        }
        
        // Draw trails if enabled
        if (this.settings.showTrails) {
            this.drawTrails();
        }
    }
    
    /**
     * Get color based on confidence score
     */
    getConfidenceColor(confidence) {
        if (confidence >= 0.8) {
            return this.colors.highConfidence;
        } else if (confidence >= 0.5) {
            return this.colors.medConfidence;
        } else {
            return this.colors.lowConfidence;
        }
    }
    
    /**
     * Add pose to trail history
     */
    addToTrail(landmarks) {
        if (!landmarks) return;
        
        this.trailHistory.push(landmarks);
        
        // Keep trail length limited
        if (this.trailHistory.length > this.maxTrailLength) {
            this.trailHistory.shift();
        }
    }
    
    /**
     * Draw movement trails
     */
    drawTrails() {
        if (this.trailHistory.length < 2) return;
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Draw trails for key points (e.g., wrists and ankles)
        const trailPoints = [15, 16, 27, 28]; // Left/right wrists and ankles
        
        trailPoints.forEach(pointIdx => {
            this.ctx.strokeStyle = this.colors.connection;
            this.ctx.lineWidth = 1;
            this.ctx.globalAlpha = 0.5;
            
            this.ctx.beginPath();
            let firstPoint = true;
            
            this.trailHistory.forEach((landmarks, idx) => {
                if (pointIdx < landmarks.length) {
                    const point = landmarks[pointIdx];
                    
                    if (point[2] > 0.5) { // Visibility threshold
                        const x = point[0] * width;
                        const y = point[1] * height;
                        
                        if (firstPoint) {
                            this.ctx.moveTo(x, y);
                            firstPoint = false;
                        } else {
                            this.ctx.lineTo(x, y);
                        }
                    }
                }
            });
            
            this.ctx.stroke();
            this.ctx.globalAlpha = 1.0;
        });
    }
    
    /**
     * Clear canvas
     */
    clear() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    /**
     * Draw text overlay
     */
    drawText(text, x, y, options = {}) {
        if (!this.ctx) return;
        
        const {
            font = '16px Arial',
            color = '#ffffff',
            background = 'rgba(0, 0, 0, 0.7)',
            padding = 8
        } = options;
        
        this.ctx.font = font;
        const metrics = this.ctx.measureText(text);
        const textWidth = metrics.width;
        const textHeight = 20; // Approximate height
        
        // Draw background
        if (background) {
            this.ctx.fillStyle = background;
            this.ctx.fillRect(
                x - padding,
                y - textHeight - padding,
                textWidth + padding * 2,
                textHeight + padding * 2
            );
        }
        
        // Draw text
        this.ctx.fillStyle = color;
        this.ctx.fillText(text, x, y);
    }
    
    /**
     * Draw info box with stats
     */
    drawInfoBox(info, position = 'top-left') {
        if (!this.ctx || !info) return;
        
        const padding = 10;
        const lineHeight = 20;
        const lines = Object.entries(info).map(([key, value]) => `${key}: ${value}`);
        
        // Calculate box dimensions
        this.ctx.font = '14px Arial';
        const maxWidth = Math.max(...lines.map(line => this.ctx.measureText(line).width));
        const boxWidth = maxWidth + padding * 2;
        const boxHeight = lines.length * lineHeight + padding * 2;
        
        // Determine position
        let x, y;
        switch (position) {
            case 'top-left':
                x = padding;
                y = padding;
                break;
            case 'top-right':
                x = this.canvas.width - boxWidth - padding;
                y = padding;
                break;
            case 'bottom-left':
                x = padding;
                y = this.canvas.height - boxHeight - padding;
                break;
            case 'bottom-right':
                x = this.canvas.width - boxWidth - padding;
                y = this.canvas.height - boxHeight - padding;
                break;
            default:
                x = padding;
                y = padding;
        }
        
        // Draw background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(x, y, boxWidth, boxHeight);
        
        // Draw border
        this.ctx.strokeStyle = '#6366f1';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x, y, boxWidth, boxHeight);
        
        // Draw text
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '14px Arial';
        lines.forEach((line, idx) => {
            this.ctx.fillText(line, x + padding, y + padding + (idx + 1) * lineHeight);
        });
    }
    
    /**
     * Draw FPS counter
     */
    drawFPS(fps) {
        this.drawText(`FPS: ${fps.toFixed(1)}`, 10, 30, {
            font: '16px monospace',
            color: '#10b981'
        });
    }
    
    /**
     * Toggle skeleton visibility
     */
    toggleSkeleton() {
        this.settings.showSkeleton = !this.settings.showSkeleton;
        return this.settings.showSkeleton;
    }
    
    /**
     * Toggle keypoints visibility
     */
    toggleKeypoints() {
        this.settings.showKeypoints = !this.settings.showKeypoints;
        return this.settings.showKeypoints;
    }
    
    /**
     * Toggle trails
     */
    toggleTrails() {
        this.settings.showTrails = !this.settings.showTrails;
        if (!this.settings.showTrails) {
            this.trailHistory = [];
        }
        return this.settings.showTrails;
    }
    
    /**
     * Update settings
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
    }
    
    /**
     * Destroy visualizer
     */
    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        this.ctx = null;
        this.canvas = null;
    }
}

// Create global instance
const visualizer = new Visualizer();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Visualizer;
}