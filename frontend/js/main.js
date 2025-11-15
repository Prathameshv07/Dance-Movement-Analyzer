/**
 * Main Application Entry Point (Simplified with Polling)
 */

import { APP_CONFIG } from './core/config.js';
import { appState } from './core/state.js';
import { apiService } from './services/api-service.js';
// import { pollingService } from './services/polling-service.js';
import { toast } from './ui/toast.js';
import { progressManager } from './ui/progress.js';
import { videoHandler } from './handlers/video-handler.js';

// DOM Elements
const elements = {
    uploadZone: document.getElementById('uploadZone'),
    fileInput: document.getElementById('fileInput'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileMeta: document.getElementById('fileMeta'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    
    uploadSection: document.getElementById('uploadSection'),
    processingSection: document.getElementById('processingSection'),
    resultsSection: document.getElementById('resultsSection'),
    
    originalVideo: document.getElementById('originalVideo'),
    analyzedVideo: document.getElementById('analyzedVideo'),
    
    movementType: document.getElementById('movementType'),
    intensityValue: document.getElementById('intensityValue'),
    intensityFill: document.getElementById('intensityFill'),
    detectionRate: document.getElementById('detectionRate'),
    framesDetected: document.getElementById('framesDetected'),
    totalFrames: document.getElementById('totalFrames'),
    confidenceScore: document.getElementById('confidenceScore'),
    smoothnessScore: document.getElementById('smoothnessScore'),
    
    bodyParts: document.getElementById('bodyParts'),
    
    newAnalysisBtn: document.getElementById('newAnalysisBtn'),
};

// Initialize
function init() {
    setupEventListeners();
    toast.info('Ready to analyze dance videos!');
}

// Event Listeners
function setupEventListeners() {
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    elements.uploadZone.addEventListener('dragover', handleDragOver);
    elements.uploadZone.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    elements.analyzeBtn.addEventListener('click', startAnalysis);
    elements.newAnalysisBtn.addEventListener('click', resetApp);
}

// File Handling
function handleDragOver(e) {
    e.preventDefault();
    elements.uploadZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) handleFile(files[0]);
}

async function handleFile(file) {
    // Validate
    if (!APP_CONFIG.ALLOWED_MIME_TYPES.includes(file.type)) {
        toast.error('Invalid file type. Please upload MP4, WebM, or AVI.');
        return;
    }
    
    if (file.size > APP_CONFIG.MAX_FILE_SIZE) {
        toast.error('File exceeds 100MB limit.');
        return;
    }
    
    appState.uploadedFile = file;
    
    // Display file info
    elements.fileName.textContent = file.name;
    elements.fileMeta.textContent = `${formatFileSize(file.size)} • ${file.type}`;
    elements.fileInfo.style.display = 'flex';
    
    // Upload
    await uploadFile(file);
}

async function uploadFile(file) {
    try {
        elements.analyzeBtn.disabled = true;
        elements.analyzeBtn.textContent = '⏳ Uploading...';
        
        const data = await apiService.uploadVideo(file);
        
        appState.setSession(data.session_id, data);
        
        // Preview original video
        const videoURL = URL.createObjectURL(file);
        elements.originalVideo.src = videoURL;
        
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = '✨ Start Analysis';
        
        toast.success('Video uploaded successfully!');
    } catch (error) {
        console.error('Upload error:', error);
        toast.error(`Upload failed: ${error.message}`);
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = '✨ Start Analysis';
    }
}

async function startAnalysis() {
    if (!appState.sessionId) {
        toast.error('Please upload a video first');
        return;
    }
    
    try {
        // Show processing section
        elements.uploadSection.style.display = 'none';
        elements.processingSection.style.display = 'block';
        
        // Start analysis
        const data = await apiService.startAnalysis(appState.sessionId);
        
        progressManager.start();
        toast.info('Analysis started!');
        
        // Connect WebSocket for real-time updates
        connectWebSocket(appState.sessionId);
        
    } catch (error) {
        console.error('Analysis error:', error);
        toast.error(`Failed to start: ${error.message}`);
        elements.uploadSection.style.display = 'block';
        elements.processingSection.style.display = 'none';
    }
}

function connectWebSocket(sessionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    console.log('🔌 Connecting WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    let heartbeatInterval;
    
    ws.onopen = () => {
        console.log('✅ WebSocket connected');
        toast.info('Connected - receiving updates');
        
        // Send heartbeat every 20 seconds
        heartbeatInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 20000);
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);
            
            switch (data.type) {
                case 'connected':
                    console.log('✅ Connected to session:', data.session_id);
                    break;
                    
                case 'progress':
                    // ✅ Update progress bar and ETA
                    const progress = data.progress || 0;
                    const message = data.message || 'Processing...';
                    
                    console.log(`📊 Progress: ${(progress * 100).toFixed(0)}%`);
                    progressManager.update(progress, message);
                    break;
                    
                case 'complete':
                    console.log('🎉 Analysis complete!');
                    clearInterval(heartbeatInterval);
                    handleAnalysisComplete(data);
                    ws.close();
                    break;
                    
                case 'error':
                    console.error('❌ Error:', data.error);
                    clearInterval(heartbeatInterval);
                    handleAnalysisError(new Error(data.error));
                    ws.close();
                    break;
                    
                case 'pong':
                    // Heartbeat response
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error, event.data);
        }
    };
    
    ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        toast.error('Connection error - progress may not update');
    };
    
    ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        clearInterval(heartbeatInterval);
    };
    
    // Store reference for cleanup
    appState.ws = ws;
}

async function handleAnalysisComplete(result) {
    progressManager.complete();
    
    // Fetch complete results
    const data = await apiService.getResults(appState.sessionId);
    appState.results = data.results;
    
    // Show results section
    elements.processingSection.style.display = 'none';
    elements.resultsSection.style.display = 'block';
    
    // Load analyzed video
    const videoUrl = apiService.getDownloadURL(appState.sessionId);
    elements.analyzedVideo.src = videoUrl;
    
    // Initialize video sync  ← ADD THIS
    videoHandler.init('originalVideo', 'analyzedVideo');  // ← ADD THIS
    
    // Display results
    displayResults(appState.results);
    
    toast.success('Analysis complete! 🎉');
}



function handleAnalysisError(error) {
    toast.error(`Analysis failed: ${error.message}`);
    elements.uploadSection.style.display = 'block';
    elements.processingSection.style.display = 'none';
    progressManager.reset();
}

function displayResults(results) {
    if (!results) return;
    
    // Movement
    const movement = results.movement_analysis;
    if (movement) {
        elements.movementType.textContent = movement.movement_type || 'Unknown';
        const intensity = Math.round(movement.intensity || 0);
        elements.intensityValue.textContent = intensity;
        elements.intensityFill.style.width = `${intensity}%`;
    }
    
    // Detection
    const processing = results.processing;
    if (processing) {
        const rate = ((processing.detection_rate || 0) * 100).toFixed(1);
        elements.detectionRate.textContent = `${rate}%`;
        elements.framesDetected.textContent = processing.frames_with_pose || 0;
        elements.totalFrames.textContent = processing.total_frames || 0;
    }
    
    // Confidence
    const pose = results.pose_analysis;
    if (pose) {
        elements.confidenceScore.textContent = (pose.average_confidence || 0).toFixed(2);
    }
    
    // Smoothness
    elements.smoothnessScore.textContent = Math.round(results.smoothness_score || 0);
    
    // Body parts
    if (movement && movement.body_part_activity) {
        displayBodyParts(movement.body_part_activity);
    }
}

function displayBodyParts(bodyParts) {
    elements.bodyParts.innerHTML = '';
    
    for (const [part, activity] of Object.entries(bodyParts)) {
        const item = document.createElement('div');
        item.className = 'body-part-item';
        
        const name = document.createElement('div');
        name.className = 'body-part-name';
        name.textContent = part.replace('_', ' ');
        
        const bar = document.createElement('div');
        bar.className = 'body-part-bar';
        
        const fill = document.createElement('div');
        fill.className = 'body-part-fill';
        fill.style.width = `${activity}%`;
        fill.textContent = `${Math.round(activity)}`;
        
        bar.appendChild(fill);
        item.appendChild(name);
        item.appendChild(bar);
        elements.bodyParts.appendChild(item);
    }
}

function resetApp() {
    appState.reset();
    progressManager.reset();
    // pollingService.stopPolling();
    
    elements.fileInfo.style.display = 'none';
    elements.uploadSection.style.display = 'block';
    elements.processingSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    
    elements.fileInput.value = '';
    elements.originalVideo.src = '';
    elements.analyzedVideo.src = '';
    
    toast.info('Ready for new analysis!');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);