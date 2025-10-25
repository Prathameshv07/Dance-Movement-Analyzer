/**
 * Main Application Logic
 * Handles UI state, file uploads, and result display
 */

const API_BASE_URL = window.location.origin;

// Application State
const AppState = {
    sessionId: null,
    uploadedFile: null,
    videoInfo: null,
    results: null,
    ws: null,
    startTime: null
};

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
    
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    processingMessage: document.getElementById('processingMessage'),
    statusValue: document.getElementById('statusValue'),
    elapsedTime: document.getElementById('elapsedTime'),
    
    originalVideo: document.getElementById('originalVideo'),
    analyzedVideo: document.getElementById('analyzedVideo'),
    downloadBtn: document.getElementById('downloadBtn'),
    
    movementType: document.getElementById('movementType'),
    intensityValue: document.getElementById('intensityValue'),
    intensityFill: document.getElementById('intensityFill'),
    detectionRate: document.getElementById('detectionRate'),
    framesDetected: document.getElementById('framesDetected'),
    totalFrames: document.getElementById('totalFrames'),
    confidenceScore: document.getElementById('confidenceScore'),
    smoothnessScore: document.getElementById('smoothnessScore'),
    
    bodyParts: document.getElementById('bodyParts'),
    rhythmCard: document.getElementById('rhythmCard'),
    bpmValue: document.getElementById('bpmValue'),
    consistencyValue: document.getElementById('consistencyValue'),
    
    newAnalysisBtn: document.getElementById('newAnalysisBtn'),
    shareBtn: document.getElementById('shareBtn'),
    toast: document.getElementById('toast')
};

// Initialize Application
function initApp() {
    setupEventListeners();
    checkBrowserCompatibility();
    showToast('Ready to analyze dance videos!', 'info');
}

// Setup Event Listeners
function setupEventListeners() {
    // Upload zone events
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    elements.uploadZone.addEventListener('dragover', handleDragOver);
    elements.uploadZone.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone.addEventListener('drop', handleDrop);
    
    // File input change
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Analyze button
    elements.analyzeBtn.addEventListener('click', startAnalysis);
    
    // Download button
    elements.downloadBtn.addEventListener('click', downloadVideo);
    
    // New analysis button
    elements.newAnalysisBtn.addEventListener('click', resetApp);
    
    // Share button
    elements.shareBtn.addEventListener('click', shareResults);
}

// File Upload Handlers
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
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// Validate and Handle File
async function handleFile(file) {
    // Validate file type
    const validTypes = ['video/mp4', 'video/webm', 'video/avi'];
    if (!validTypes.includes(file.type)) {
        showToast('Please upload a valid video file (MP4, WebM, AVI)', 'error');
        return;
    }
    
    // Validate file size (100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('File size exceeds 100MB limit', 'error');
        return;
    }
    
    AppState.uploadedFile = file;
    
    // Display file info
    elements.fileName.textContent = file.name;
    elements.fileMeta.textContent = `${formatFileSize(file.size)} • ${file.type}`;
    elements.fileInfo.style.display = 'flex';
    
    // Upload file to server
    await uploadFile(file);
}

// Upload File to Server
async function uploadFile(file) {
    try {
        elements.analyzeBtn.disabled = true;
        elements.analyzeBtn.textContent = '⏳ Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const data = await response.json();
        
        AppState.sessionId = data.session_id;
        AppState.videoInfo = data;
        
        // Create object URL for original video preview
        const videoURL = URL.createObjectURL(file);
        elements.originalVideo.src = videoURL;
        
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = '✨ Start Analysis';
        
        showToast('Video uploaded successfully!', 'success');
        
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Failed to upload video. Please try again.', 'error');
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = '✨ Start Analysis';
    }
}

// Start Analysis
async function startAnalysis() {
    if (!AppState.sessionId) {
        showToast('Please upload a video first', 'error');
        return;
    }
    
    try {
        // Show processing section
        elements.uploadSection.style.display = 'none';
        elements.processingSection.style.display = 'block';
        
        // Initialize WebSocket
        initWebSocket(AppState.sessionId);
        
        // Start analysis
        const response = await fetch(`${API_BASE_URL}/api/analyze/${AppState.sessionId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed to start');
        }
        
        const data = await response.json();
        
        AppState.startTime = Date.now();
        startElapsedTimer();
        
        showToast('Analysis started!', 'info');
        
    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Failed to start analysis. Please try again.', 'error');
        elements.uploadSection.style.display = 'block';
        elements.processingSection.style.display = 'none';
    }
}

// Initialize WebSocket
function initWebSocket(sessionId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${sessionId}`;
    
    AppState.ws = new WebSocket(wsUrl);
    
    AppState.ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    AppState.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    AppState.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    AppState.ws.onclose = () => {
        console.log('WebSocket closed');
    };
    
    // Send heartbeat every 20 seconds
    setInterval(() => {
        if (AppState.ws && AppState.ws.readyState === WebSocket.OPEN) {
            AppState.ws.send('ping');
        }
    }, 20000);
}

// Handle WebSocket Messages
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'connected':
            console.log('WebSocket ready');
            break;
            
        case 'progress':
            updateProgress(message.progress, message.message);
            break;
            
        case 'status':
            elements.statusValue.textContent = message.status;
            elements.processingMessage.textContent = message.message;
            break;
            
        case 'complete':
            handleAnalysisComplete(message);
            break;
            
        case 'error':
            handleAnalysisError(message);
            break;
            
        case 'pong':
            // Heartbeat response
            break;
    }
}

// Update Progress
function updateProgress(progress, message) {
    const percentage = Math.round(progress * 100);
    elements.progressFill.style.width = `${percentage}%`;
    elements.progressText.textContent = `${percentage}%`;
    elements.processingMessage.textContent = message;
}

// Start Elapsed Timer
function startElapsedTimer() {
    const timer = setInterval(() => {
        if (AppState.startTime) {
            const elapsed = Math.floor((Date.now() - AppState.startTime) / 1000);
            elements.elapsedTime.textContent = `${elapsed}s`;
        } else {
            clearInterval(timer);
        }
    }, 1000);
}

// Handle Analysis Complete
async function handleAnalysisComplete(message) {
    AppState.results = message.results;
    AppState.startTime = null;
    
    // Hide processing, show results
    elements.processingSection.style.display = 'none';
    elements.resultsSection.style.display = 'block';
    
    // Load analyzed video
    const videoUrl = `${API_BASE_URL}/api/download/${AppState.sessionId}`;
    elements.analyzedVideo.src = videoUrl;
    
    // Display results
    displayResults(AppState.results);
    
    // Close WebSocket
    if (AppState.ws) {
        AppState.ws.close();
        AppState.ws = null;
    }
    
    showToast('Analysis complete!', 'success');
}

// Handle Analysis Error
function handleAnalysisError(message) {
    showToast(message.message, 'error');
    elements.uploadSection.style.display = 'block';
    elements.processingSection.style.display = 'none';
    AppState.startTime = null;
}

// Display Results
function displayResults(results) {
    // Movement Classification
    const movement = results.movement_analysis;
    if (movement) {
        elements.movementType.textContent = movement.movement_type;
        elements.intensityValue.textContent = Math.round(movement.intensity);
        elements.intensityFill.style.width = `${movement.intensity}%`;
    }
    
    // Detection Stats
    const processing = results.processing;
    const detectionRate = (processing.detection_rate * 100).toFixed(1);
    elements.detectionRate.textContent = `${detectionRate}%`;
    elements.framesDetected.textContent = processing.frames_with_pose;
    elements.totalFrames.textContent = processing.total_frames;
    
    // Confidence
    const poseAnalysis = results.pose_analysis;
    elements.confidenceScore.textContent = poseAnalysis.average_confidence.toFixed(2);
    
    // Smoothness
    elements.smoothnessScore.textContent = Math.round(results.smoothness_score);
    
    // Body Parts
    if (movement && movement.body_part_activity) {
        displayBodyParts(movement.body_part_activity);
    }
    
    // Rhythm
    const rhythm = results.rhythm_analysis;
    if (rhythm && rhythm.has_rhythm) {
        elements.rhythmCard.style.display = 'block';
        elements.bpmValue.textContent = Math.round(rhythm.estimated_bpm);
        elements.consistencyValue.textContent = `${Math.round(rhythm.rhythm_consistency * 100)}%`;
    }
}

// Display Body Parts Activity
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

// Download Video
function downloadVideo() {
    if (!AppState.sessionId) return;
    
    const url = `${API_BASE_URL}/api/download/${AppState.sessionId}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `analyzed_${AppState.uploadedFile?.name || 'video.mp4'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    showToast('Download started!', 'success');
}

// Share Results
function shareResults() {
    const text = `Check out my dance movement analysis! Movement: ${elements.movementType.textContent}, Intensity: ${elements.intensityValue.textContent}/100`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Dance Movement Analysis',
            text: text
        }).catch(console.error);
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(text).then(() => {
            showToast('Results copied to clipboard!', 'success');
        }).catch(() => {
            showToast('Could not share results', 'error');
        });
    }
}

// Reset App
function resetApp() {
    // Reset state
    AppState.sessionId = null;
    AppState.uploadedFile = null;
    AppState.videoInfo = null;
    AppState.results = null;
    AppState.startTime = null;
    
    // Reset UI
    elements.fileInfo.style.display = 'none';
    elements.uploadSection.style.display = 'block';
    elements.processingSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    
    elements.fileInput.value = '';
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = '0%';
    
    // Clear videos
    elements.originalVideo.src = '';
    elements.analyzedVideo.src = '';
    
    showToast('Ready for new analysis!', 'info');
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

function checkBrowserCompatibility() {
    if (!window.WebSocket) {
        showToast('Your browser does not support WebSocket. Real-time updates may not work.', 'error');
    }
    
    if (!window.FileReader) {
        showToast('Your browser does not support file reading.', 'error');
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', initApp);