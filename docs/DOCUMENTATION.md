# DanceDynamics - Technical Documentation

## 1. Project Overview

The DanceDynamics is an AI-powered web application that leverages advanced computer vision and machine learning technologies to provide comprehensive analysis of dance movements. Using MediaPipe's pose estimation, the system detects 33 body keypoints, classifies movements into distinct categories, tracks individual body part activities, detects rhythmic patterns, and generates detailed analytics with visual overlays, transforming raw video into actionable insights for dancers, coaches, and researchers.

## 2. Objective

The primary objective of the DanceDynamics is to democratize movement analysis by providing:

- **Accurate Pose Detection**: Utilizing MediaPipe Pose to track 33 body landmarks with 95%+ accuracy
- **Movement Classification**: Categorizing movements into 5 distinct types (Standing, Walking, Dancing, Jumping, Crouching)
- **Intensity Scoring**: Quantifying movement energy on a 0-100 scale
- **Body Part Tracking**: Individual activity monitoring for 6 body regions (head, torso, arms, legs)
- **Rhythm Analysis**: Detecting musical patterns and estimating BPM for dance sequences
- **Real-time Processing**: WebSocket-powered live updates during analysis
- **Interactive Visualization**: Modern glassmorphism UI with skeleton overlay rendering
- **Multiple Export Formats**: JSON, video with overlay, downloadable results
- **Production-Ready Architecture**: Containerized deployment with comprehensive testing

## 3. Core Features

### **Advanced Pose Detection**
AI-powered pose estimation with precision tracking:

- **MediaPipe Integration**: State-of-the-art pose detection from Google Research
- **33 Keypoints**: Full-body landmark tracking including face, torso, arms, and legs
- **Confidence Scoring**: Per-keypoint visibility and confidence metrics (0.0-1.0)
- **Smooth Tracking**: Temporal filtering for stable landmark positions
- **Real-time Processing**: 30 FPS target processing speed (0.8-1.2x realtime)

### **Movement Classification System**
Intelligent movement categorization:

- **5 Movement Types**:
  - **Standing**: Minimal movement (velocity < 0.01)
  - **Walking**: Moderate linear displacement (velocity 0.01-0.03)
  - **Dancing**: Dynamic varied movement (velocity 0.03-0.06)
  - **Jumping**: High vertical displacement (velocity > 0.12)
  - **Crouching**: Compressed posture with low center of mass
- **Velocity-based Detection**: Frame-to-frame landmark displacement analysis
- **Intensity Scoring**: 0-100 scale based on movement magnitude and frequency
- **Smoothness Analysis**: Jerk-based quality metrics for movement fluidity

### **Body Part Activity Tracking**
Granular movement analysis for individual body regions:

- **6 Body Regions Tracked**:
  - Head (nose, eyes, ears)
  - Torso (shoulders, hips)
  - Left Arm (shoulder, elbow, wrist)
  - Right Arm (shoulder, elbow, wrist)
  - Left Leg (hip, knee, ankle)
  - Right Leg (hip, knee, ankle)
- **Activity Scores**: 0-100 scale per body part
- **Comparative Analysis**: Identify asymmetries and movement patterns
- **Visual Representation**: Animated bar charts in results dashboard

### **Rhythm Detection**
Musical pattern recognition for dance analysis:

- **BPM Estimation**: Automatic beat-per-minute calculation
- **Peak Detection**: Identifies rhythmic movement peaks
- **Consistency Scoring**: Measures rhythm stability (0-100%)
- **Pattern Recognition**: Detects repetitive movement sequences

### **Real-time Communication**
WebSocket-powered live updates:

- **Progress Tracking**: Frame-by-frame processing status (0.0-1.0)
- **Status Messages**: Descriptive updates for each processing stage
- **Bidirectional Communication**: Client-server real-time messaging
- **Auto-reconnection**: Resilient connection management
- **Heartbeat Mechanism**: Connection health monitoring

### **Modern Web Interface**
Glassmorphism design with smooth animations:

- **Responsive Layout**: Mobile, tablet, and desktop support
- **Dark Theme**: Eye-friendly color scheme with gradient backgrounds
- **Smooth Animations**: GPU-accelerated transitions and effects
- **Interactive Elements**: Hover effects, loading states, toast notifications
- **Video Comparison**: Side-by-side original and analyzed playback
- **Accessibility**: WCAG AA compliant design

## 4. Technologies and Tools

### **Backend Stack**

- **Programming Language**: Python 3.10+
- **Web Framework**: FastAPI 0.104+ with Uvicorn ASGI server
- **AI/ML Libraries**:
  - **MediaPipe 0.10+**: Pose detection and landmark tracking
  - **OpenCV 4.8+**: Video processing and frame manipulation
  - **NumPy 1.24+**: Numerical computations and array operations
  - **SciPy 1.11+**: Scientific computing for signal processing
- **Video Processing**:
  - **FFmpeg**: Video encoding/decoding
  - **opencv-python**: Computer vision operations
  - **numpy**: Frame array manipulation
- **API Features**:
  - **python-multipart**: File upload handling
  - **aiofiles**: Async file operations
  - **websockets**: Real-time bidirectional communication
  - **pydantic**: Data validation and settings management

### **Frontend Stack**

- **HTML5**: Semantic markup and structure
- **CSS3**: Glassmorphism design with animations
  - Backdrop filters for glass effects
  - CSS Grid and Flexbox layouts
  - Custom animations and transitions
- **Vanilla JavaScript (ES6+)**:
  - Async/await for API calls
  - WebSocket API for real-time updates
  - File API for uploads
  - Canvas API for visualizations
- **No Framework Dependencies**: Maximum browser compatibility

### **DevOps & Deployment**

- **Containerization**: Docker 20.10+ with multi-stage builds
- **Orchestration**: Docker Compose 1.29+
- **Testing**:
  - **pytest 7.4+**: Unit and integration testing
  - **pytest-cov**: Code coverage reporting
  - **pytest-asyncio**: Async test support
  - **aiohttp**: Load testing client
- **CI/CD**: GitHub Actions ready
- **Monitoring**: Health check endpoints, logging

## 5. System Requirements

### **Minimum Requirements**

- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **CPU**: Intel i5-8400 or AMD Ryzen 5 2600 (4 cores)
- **RAM**: 8GB
- **Storage**: 2GB for application + models
- **Network**: Internet for initial setup
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### **Recommended Configuration**

- **CPU**: Intel i7-9700 or AMD Ryzen 7 3700X (8 cores)
- **RAM**: 16GB+
- **Storage**: 10GB+ (for uploads and outputs)
- **GPU**: Optional NVIDIA GPU with 4GB+ VRAM
- **Network**: Stable broadband connection

### **Docker Requirements**

- **Docker**: 20.10 or later
- **Docker Compose**: 1.29 or later
- **Available Disk**: 10GB (for images and volumes)

## 6. Setup Instructions

### **a. Local Development Setup**

#### **Step 1: Clone Repository**
```bash
git clone https://github.com/Prathameshv07/DanceDynamics.git
cd DanceDynamics
```

#### **Step 2: Backend Setup**
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Step 3: Configuration**
```bash
# Create environment file (optional)
cp .env.example .env

# Edit .env with your preferences
# API_HOST=0.0.0.0
# API_PORT=7860
# DEBUG=false
# MAX_FILE_SIZE=104857600
```

#### **Step 4: Run Application**
```bash
# Start server
python app/main.py

# Or use uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

#### **Step 5: Access Application**
- **Web Interface**: http://localhost:7860
- **API Documentation**: http://localhost:7860/api/docs
- **Health Check**: http://localhost:7860/health

### **b. Docker Deployment**

#### **Step 1: Build Image**
```bash
# From project root
docker-compose build
```

#### **Step 2: Start Services**
```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

#### **Step 3: Access Application**
- **Web Interface**: http://localhost:7860
- **API Documentation**: http://localhost:7860/api/docs

#### **Step 4: Manage Services**
```bash
# Stop services
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps
```

### **c. Production Deployment**

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides on:
- AWS EC2 deployment
- Google Cloud Run
- Hugging Face Spaces
- DigitalOcean App Platform
- Custom server deployment

## 7. Detailed Project Structure

```
DanceDynamics/
│
├── backend/                              # Backend application
│   ├── app/                              # Main application package
│   │   ├── __init__.py                   # Package initialization
│   │   ├── config.py                     # Configuration (45 LOC)
│   │   │   # - Environment variables
│   │   │   # - MediaPipe settings
│   │   │   # - File size limits
│   │   │   # - Supported formats
│   │   │
│   │   ├── utils.py                      # Utilities (105 LOC)
│   │   │   # - File validation
│   │   │   # - UUID generation
│   │   │   # - JSON formatters
│   │   │   # - Logging utilities
│   │   │
│   │   ├── pose_analyzer.py              # Pose Detection (256 LOC)
│   │   │   # - MediaPipe integration
│   │   │   # - 33 keypoint detection
│   │   │   # - Confidence scoring
│   │   │   # - Skeleton overlay rendering
│   │   │
│   │   ├── movement_classifier.py        # Classification (185 LOC)
│   │   │   # - 5 movement types
│   │   │   # - Intensity calculation
│   │   │   # - Body part tracking
│   │   │   # - Rhythm detection
│   │   │
│   │   ├── video_processor.py            # Video Processing (208 LOC)
│   │   │   # - Video I/O operations
│   │   │   # - Frame extraction
│   │   │   # - Overlay rendering
│   │   │   # - Video encoding
│   │   │
│   │   └── main.py                       # FastAPI Application (500 LOC)
│   │       # - REST API endpoints (7)
│   │       # - WebSocket endpoint
│   │       # - Session management
│   │       # - Background tasks
│   │
│   ├── tests/                            # Test Suite
│   │   ├── __init__.py
│   │   ├── test_pose_analyzer.py         # 15 unit tests
│   │   ├── test_movement_classifier.py   # 20 unit tests
│   │   ├── test_api.py                   # 20 API tests
│   │   ├── test_integration.py           # 15 integration tests
│   │   └── test_load.py                  # Load testing
│   │
│   ├── uploads/                          # Upload directory (auto-created)
│   ├── outputs/                          # Output directory (auto-created)
│   ├── requirements.txt                  # Python dependencies
│   └── run_all_tests.py                  # Master test runner
│
├── frontend/                             # Frontend application
│   ├── index.html                        # Main UI (300 LOC)
│   │   # - Upload section
│   │   # - Processing section
│   │   # - Results section
│   │   # - Footer
│   │
│   ├── css/
│   │   └── styles.css                    # Glassmorphism design (500 LOC)
│   │       # - Dark theme
│   │       # - Glass effects
│   │       # - Animations
│   │       # - Responsive layout
│   │
│   └── js/
│       ├── app.js                        # Main logic (800 LOC)
│       │   # - State management
│       │   # - File upload
│       │   # - API communication
│       │   # - UI updates
│       │
│       ├── video-handler.js              # Video utilities (200 LOC)
│       │   # - Video validation
│       │   # - Playback sync
│       │   # - Metadata extraction
│       │
│       ├── websocket-client.js           # WebSocket manager (150 LOC)
│       │   # - Connection management
│       │   # - Auto-reconnection
│       │   # - Message routing
│       │
│       └── visualization.js              # Canvas rendering (180 LOC)
│           # - Skeleton drawing
│           # - Movement trails
│           # - Overlays
│
├── docs/                                 # Documentation
│   ├── DEPLOYMENT.md                    # Deployment guides
│   ├── DOCUMENTATION.md                 # This file
│   └── screenshots/                     # UI screenshots
│
├── Dockerfile                           # Multi-stage Docker build
├── docker-compose.yml                   # Docker Compose configuration
├── .dockerignore                        # Docker build exclusions
├── .gitignore                          # Git exclusions
├── LICENSE                             # MIT License
└── README.md                           # Project overview

```

## 8. Core Components Deep Dive

### **8.1 Pose Analyzer (pose_analyzer.py)**

**Purpose**: Detect human pose and extract 33 body landmarks using MediaPipe.

**Key Classes:**
```python
class PoseAnalyzer:
    """MediaPipe-based pose detection engine"""
    
    def __init__(self, model_complexity=1, min_detection_confidence=0.5)
    def process_frame(self, frame, frame_idx, timestamp) -> PoseResult
    def process_video_batch(self, frames) -> List[PoseResult]
    def draw_skeleton_overlay(self, frame, pose_result) -> np.ndarray
    def get_keypoints_array(self, pose_result) -> np.ndarray
```

**MediaPipe Landmarks (33 keypoints):**
```
0: nose                17: left_pinky
1: left_eye_inner      18: right_pinky
2: left_eye            19: left_index
3: left_eye_outer      20: right_index
4: right_eye_inner     21: left_thumb
5: right_eye           22: right_thumb
6: right_eye_outer     23: left_hip
7: left_ear            24: right_hip
8: right_ear           25: left_knee
9: mouth_left          26: right_knee
10: mouth_right        27: left_ankle
11: left_shoulder      28: right_ankle
12: right_shoulder     29: left_heel
13: left_elbow         30: right_heel
14: right_elbow        31: left_foot_index
15: left_wrist         32: right_foot_index
16: right_wrist
```

**Processing Pipeline:**
1. Load video with OpenCV
2. Extract frames sequentially
3. Convert BGR to RGB
4. Process with MediaPipe Pose
5. Extract 33 landmarks with confidence scores
6. Draw skeleton overlay on original frame
7. Return structured PoseResult objects

**Optimization Techniques:**
- Batch frame processing
- Model complexity configuration (0-2)
- Confidence thresholding
- Temporal smoothing
- Memory-efficient buffering

### **8.2 Movement Classifier (movement_classifier.py)**

**Purpose**: Classify movements and calculate body part activities.

**Key Classes:**
```python
class MovementClassifier:
    """Advanced movement classification engine"""
    
    def analyze_sequence(self, keypoints_sequence) -> MovementMetrics
    def _calculate_velocities(self, keypoints_sequence) -> np.ndarray
    def _classify_movement_type(self, velocity) -> MovementType
    def _calculate_intensity(self, velocities) -> float
    def _calculate_body_part_activity(self, keypoints_sequence) -> Dict
    def detect_rhythm_patterns(self, keypoints_sequence) -> RhythmAnalysis
    def calculate_movement_smoothness(self, keypoints_sequence) -> float
```

**Movement Classification Logic:**
```python
# Velocity thresholds
VELOCITY_STANDING = 0.01    # Minimal movement
VELOCITY_WALKING = 0.03     # Moderate linear
VELOCITY_DANCING = 0.06     # Dynamic varied
VELOCITY_JUMPING = 0.12     # High vertical

# Classification algorithm
if velocity < VELOCITY_STANDING:
    return MovementType.STANDING
elif velocity < VELOCITY_WALKING:
    return MovementType.WALKING
elif velocity < VELOCITY_DANCING:
    return MovementType.DANCING
elif velocity < VELOCITY_JUMPING:
    return MovementType.DANCING  # High-intensity dance
else:
    return MovementType.JUMPING
```

**Body Part Definitions:**
```python
BODY_PARTS = {
    'head': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Face landmarks
    'torso': [11, 12, 23, 24],                    # Shoulders + hips
    'left_arm': [11, 13, 15, 17, 19, 21],        # Left arm chain
    'right_arm': [12, 14, 16, 18, 20, 22],       # Right arm chain
    'left_leg': [23, 25, 27, 29, 31],            # Left leg chain
    'right_leg': [24, 26, 28, 30, 32]            # Right leg chain
}
```

**Rhythm Detection:**
- FFT-based frequency analysis
- Peak detection in movement signal
- BPM calculation from peak intervals
- Consistency scoring via variance analysis

### **8.3 Video Processor (video_processor.py)**

**Purpose**: Handle video I/O and processing pipeline.

**Key Classes:**
```python
class VideoProcessor:
    """Complete video processing pipeline"""
    
    def __init__(self, pose_analyzer, movement_classifier)
    def load_video(self, video_path) -> VideoMetadata
    def process_video(self, video_path, output_path, progress_callback) -> Dict
    def extract_frame(self, video_path, frame_idx) -> np.ndarray
    def create_thumbnail(self, video_path) -> bytes
```

**Processing Workflow:**
```
1. Video Loading
   ├─ Open with cv2.VideoCapture
   ├─ Extract metadata (fps, duration, resolution)
   └─ Validate format and codec

2. Frame Processing
   ├─ Extract frames sequentially
   ├─ Process with PoseAnalyzer
   ├─ Draw skeleton overlay
   └─ Update progress via callback

3. Movement Analysis
   ├─ Collect all pose results
   ├─ Analyze with MovementClassifier
   └─ Generate metrics

4. Video Encoding
   ├─ Create VideoWriter
   ├─ Write processed frames
   ├─ Apply H.264 codec
   └─ Save to output path

5. Results Generation
   ├─ Combine pose + movement data
   ├─ Calculate statistics
   └─ Return comprehensive results
```

**Supported Formats:**
- Input: MP4, WebM, AVI, MOV, MKV
- Output: MP4 (H.264 codec)

### **8.4 FastAPI Application (main.py)**

**Purpose**: RESTful API server with WebSocket support.

**API Endpoints:**

```python
# Upload video
@app.post("/api/upload")
async def upload_video(file: UploadFile) -> dict:
    """
    Upload and validate video file
    Returns: session_id, file_info, metadata
    """

# Start analysis
@app.post("/api/analyze/{session_id}")
async def start_analysis(session_id: str, background_tasks: BackgroundTasks) -> dict:
    """
    Trigger async video processing
    Returns: session_id, websocket_url
    """

# Get results
@app.get("/api/results/{session_id}")
async def get_results(session_id: str) -> dict:
    """
    Retrieve processing results
    Returns: status, results, download_url
    """

# Download video
@app.get("/api/download/{session_id}")
async def download_video(session_id: str) -> FileResponse:
    """
    Download processed video with overlay
    Returns: video/mp4 file
    """

# WebSocket connection
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Real-time bidirectional communication
    Messages: connected, progress, status, complete, error
    """

# Health check
@app.get("/health")
async def health_check() -> dict:
    """
    System health and status
    Returns: status, timestamp, active_sessions
    """

# List sessions
@app.get("/api/sessions")
async def list_sessions() -> dict:
    """
    Get all active sessions
    Returns: count, sessions[]
    """

# Delete session
@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """
    Remove session and cleanup files
    Returns: success, message
    """
```

**Session Management:**
```python
# In-memory session store
processing_sessions = {
    "session_id": {
        "status": "pending|processing|completed|failed",
        "filename": "original_filename.mp4",
        "upload_path": "/uploads/uuid.mp4",
        "output_path": "/outputs/uuid_analyzed.mp4",
        "results": {...},  # Analysis results
        "progress": 0.0,   # 0.0 to 1.0
        "message": "Status message",
        "created_at": "2024-10-25T10:30:00"
    }
}
```

**Background Processing:**
```python
async def process_video_background(session_id: str):
    """
    Async background task for video processing
    Updates session status and sends WebSocket messages
    """
    try:
        # Update status
        session["status"] = "processing"
        
        # Process video
        results = processor.process_video(
            video_path,
            output_path,
            progress_callback=lambda p, m: send_progress(p, m)
        )
        
        # Update session
        session["status"] = "completed"
        session["results"] = results
        
        # Notify via WebSocket
        await send_complete_message(session_id, results)
        
    except Exception as e:
        session["status"] = "failed"
        await send_error_message(session_id, str(e))
```

### **8.5 Frontend Architecture**

**HTML Structure (index.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <!-- Meta tags, title, Tailwind CDN -->
</head>
<body>
    <!-- Header -->
    <header>Logo, Title, Tagline</header>
    
    <!-- Upload Section -->
    <section id="upload-section">
        <div class="dropzone">Drag & Drop</div>
        <div class="file-info">File details</div>
        <button>Start Analysis</button>
    </section>
    
    <!-- Processing Section -->
    <section id="processing-section">
        <div class="progress-bar"></div>
        <div class="status-message"></div>
        <div class="elapsed-time"></div>
    </section>
    
    <!-- Results Section -->
    <section id="results-section">
        <div class="video-comparison">
            <video id="original"></video>
            <video id="analyzed"></video>
        </div>
        <div class="metrics-dashboard">
            <!-- Movement, Detection, Confidence, Smoothness cards -->
        </div>
        <div class="body-parts-activity">
            <!-- 6 activity bars -->
        </div>
        <div class="rhythm-analysis">
            <!-- BPM, consistency -->
        </div>
        <button>Download</button>
    </section>
    
    <!-- Scripts -->
    <script src="js/video-handler.js"></script>
    <script src="js/websocket-client.js"></script>
    <script src="js/visualization.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

**JavaScript Modules:**

**app.js** - Main application logic
```javascript
// State management
const AppState = {
    sessionId: null,
    uploadedFile: null,
    videoInfo: null,
    results: null,
    ws: null
};

// Main functions
async function uploadFile(file)
async function startAnalysis()
async function displayResults(results)
function setupVideoSync()
function downloadVideo()
```

**websocket-client.js** - WebSocket manager
```javascript
class WebSocketClient {
    constructor(sessionId, onMessage)
    connect()
    disconnect()
    sendHeartbeat()
    handleMessage(message)
    reconnect()
}
```

**video-handler.js** - Video utilities
```javascript
class VideoHandler {
    init(originalId, analyzedId)
    syncPlayback()
    syncSeeking()
    validateFile(file)
    extractMetadata(file)
}
```

**visualization.js** - Canvas rendering
```javascript
class Visualizer {
    init(canvasId)
    drawSkeleton(landmarks, confidence)
    drawKeypoints(landmarks)
    drawTrails(history)
    clear()
}
```

## 9. API Documentation

### **9.1 Request/Response Examples**

**Upload Video:**
```bash
curl -X POST http://localhost:7860/api/upload \
  -F "file=@dance.mp4"

# Response:
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "dance.mp4",
  "size": "15.2 MB",
  "duration": "10.5s",
  "resolution": "1920x1080",
  "fps": 30.0,
  "frame_count": 315
}
```

**Start Analysis:**
```bash
curl -X POST http://localhost:7860/api/analyze/550e8400-e29b-41d4-a716-446655440000

# Response:
{
  "success": true,
  "message": "Analysis started",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "websocket_url": "/ws/550e8400-e29b-41d4-a716-446655440000"
}
```

**Get Results:**
```bash
curl http://localhost:7860/api/results/550e8400-e29b-41d4-a716-446655440000

# Response:
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "processing": {
      "total_frames": 315,
      "frames_with_pose": 308,
      "detection_rate": 0.978,
      "processing_time": 12.5
    },
    "pose_analysis": {
      "average_confidence": 0.87,
      "total_keypoints": 308
    },
    "movement_analysis": {
      "movement_type": "Dancing",
      "intensity": 68.5,
      "velocity": 0.0734,
      "body_part_activity": {
        "head": 15.2,
        "torso": 25.8,
        "left_arm": 62.3,
        "right_arm": 58.7,
        "left_leg": 42.1,
        "right_leg": 43.5
      }
    },
    "rhythm_analysis": {
      "has_rhythm": true,
      "estimated_bpm": 128.4,
      "rhythm_consistency": 73
    },
    "smoothness_score": 78.3
  },
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

**WebSocket Messages:**
```javascript
// Connected
{
  "type": "connected",
  "message": "WebSocket connected",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}

// Progress
{
  "type": "progress",
  "progress": 0.45,
  "message": "Processing frame 142/315",
  "timestamp": "2024-10-25T10:32:15"
}

// Complete
{
  "type": "complete",
  "status": "completed",
  "message": "Analysis complete!",
  "results": {...},
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
}
```

## 10. Testing Strategy

### **10.1 Test Coverage**

```
Total Tests: 70+
├── Unit Tests: 35
│   ├── Pose Analyzer: 15
│   └── Movement Classifier: 20
├── API Tests: 20
├── Integration Tests: 15
└── Load Tests: Performance benchmarks

Coverage: 95%+
```

### **10.2 Running Tests**

```bash
# All tests
python run_all_tests.py

# Specific suites
pytest tests/test_pose_analyzer.py -v
pytest tests/test_movement_classifier.py -v
pytest tests/test_api.py -v
pytest tests/test_integration.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Load testing
python tests/test_load.py
```

## 11. Deployment Architecture

### **11.1 Docker Architecture**

```
Multi-Stage Build:
├── Stage 1: Base (Python 3.10-slim + system deps)
├── Stage 2: Dependencies (Python packages)
└── Stage 3: Production (App code + non-root user)

Image Size: ~1GB (optimized)
Build Time: 3-5 minutes
Startup Time: < 10 seconds
```

### **11.2 Deployment Options**

| Platform | Setup Time | Cost/Month | Best For |
|----------|-----------|------------|----------|
| Local Docker | 5 min | $0 | Development |
| Hugging Face | 10 min | $0-15 | Demos |
| AWS EC2 | 20 min | $30-40 | Production |
| Google Cloud Run | 15 min | $10-50 | Variable load |
| DigitalOcean | 10 min | $12-24 | Simple deploy |

## 12. Security Considerations

- ✅ Input validation (file type, size, format)
- ✅ Path traversal prevention
- ✅ Non-root Docker user (UID 1000)
- ✅ CORS configuration
- ✅ Session isolation
- ✅ Secure WebSocket connections
- ✅ Environment variable secrets
- ✅ Rate limiting (optional)
- ✅ Error message sanitization

## 13. Performance Optimization

### **13.1 Backend Optimizations**
- Batch frame processing
- Memory-efficient buffering
- INT8 quantization (optional)
- Async video processing
- Model caching

### **13.2 Frontend Optimizations**
- Vanilla JS (no framework overhead)
- Efficient WebSocket handling
- Canvas rendering optimization
- Lazy loading
- GPU-accelerated CSS animations

### **13.3 Docker Optimizations**
- Multi-stage builds
- Layer caching
- Minimal base image
- .dockerignore
- Health check efficiency

## 14. License

MIT License - See [LICENSE](LICENSE) file.

## 14. Support & Contact

- **Documentation**: docs/ folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions