# AI Task Worker System

Một hệ thống phân tán để quản lý và thực thi các AI task với Celery, MongoDB và MinIO.

## 🚀 Tính Năng Chính

- **Dynamic Task Loading**: Load task từ MinIO và cache locally
- **Celery Integration**: Hệ thống queue phân tán với Redis
- **Pipeline Support**: Thực thi chuỗi tasks tuần tự hoặc song song
- **Database Tracking**: Lưu trữ metadata và execution history trong MongoDB
- **File Storage**: Lưu trữ task code trong MinIO (S3-compatible)
- **Health Monitoring**: Worker status và health check tự động
- **CLI Tools**: Công cụ quản lý tasks và workers
- **Configuration Management**: Config linh hoạt với validation

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     MongoDB     │    │      MinIO      │    │      Redis      │
│  (Metadata +    │    │  (Task Storage) │    │   (Message      │
│   History)      │    │                 │    │    Broker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────────┐
         │                AI Worker Nodes                      │
         │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
         │  │   Worker 1  │  │   Worker 2  │  │   Worker N  │ │
         │  │  - Celery   │  │  - Celery   │  │  - Celery   │ │
         │  │  - Tasks    │  │  - Tasks    │  │  - Tasks    │ │
         │  │  - Monitor  │  │  - Monitor  │  │  - Monitor  │ │
         │  └─────────────┘  └─────────────┘  └─────────────┘ │
         └─────────────────────────────────────────────────────┘
```

## 📋 Yêu Cầu Hệ Thống

- Python 3.8+
- Docker & Docker Compose
- 4GB RAM (tối thiểu)
- 10GB disk space

## ⚡ Cài Đặt & Khởi Động

### 1. Clone Repository & Setup

```bash
git clone <repository-url>
cd ai-task-worker

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Start MongoDB, MinIO, Redis
docker-compose up -d

# Check services status
docker-compose ps
```

### 3. Initialize System

```bash
# Initialize system components
python3 scripts/init_system.py
```

## 🚀 Quick Start - Run Existing Tasks & Pipelines

### Prerequisites
- All services running: MongoDB, MinIO, Redis
- Python dependencies installed
- Test image available (`test.jpg`)

### 🎯 Available Tasks (Ready to Run)

The system comes with these pre-configured tasks:

| Task ID | Description | Input | Queue | Priority |
|---------|-------------|-------|-------|----------|
| `face_detection` | Detect faces in images | `{"image_path": "test.jpg"}` | `face_detection` | 8 |
| `face_attribute` | Extract face attributes (age, gender, emotion) | Face detection results | `face_attribute` | 6 |
| `face_extractor` | Extract face feature vectors | Face detection results | `face_extractor` | 6 |
| `simple_face_detector` | Basic face detection | `{"image_path": "test.jpg"}` | `default` | 5 |
| `text_sentiment` | Analyze text sentiment | `{"text": "Hello world!"}` | `nlp` | 5 |

### 🔗 Available Pipelines (Ready to Run)

| Pipeline ID | Description | Input | Processing |
|-------------|-------------|-------|------------|
| `simple_face_pipeline` | Basic face detection only | `{"image_path": "test.jpg"}` | Sequential |
| `face_processing_pipeline` | Face detection + attributes + features | `{"image_path": "test.jpg"}` | Parallel execution |

### ⚡ Instant Demo Commands

#### 1. Quick Pipeline Execution (No Workers Needed)
```bash
# Simple face detection pipeline
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'

# Complex face processing pipeline
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
```

#### 2. Direct Task Testing
```bash
# Test face detection
python3 -m tools.task_manager test face_detection '"test.jpg"'

# Test sentiment analysis
python3 -m tools.task_manager test text_sentiment '"This is amazing!"'

# Test simple face detector
python3 -m tools.task_manager test simple_face_detector '"test.jpg"'
```

#### 3. Run Pre-built Demo Scripts
```bash
# Complete face processing demo
python demo_face_processing.py

# Simple registration demo
python simple_registration_demo.py

# JSON pipeline demo
python json_pipeline_demo.py

# Windows quick demo
run_demo.bat

# Linux/Mac quick demo
./run_demo.sh
```

### 🎯 Complete Demo Workflow

#### Prerequisites for Advanced Features
- All services running: MongoDB, MinIO, Redis
- Python dependencies installed
- Test image available (`test.jpg`)

### Step 1: Create & Register Tasks

```bash
# Create new task from template
python3 -m tools.task_manager create simple_face_detector --template simple

# Register task in the system
python3 -m tools.task_manager register tasks/simple_face_detector

# Verify registration
python3 -m tools.task_manager list
python3 -m tools.task_manager info simple_face_detector
```

### Step 2: Start Workers

```bash
# Start specific task worker
python3 -m scripts.start_worker start --task simple_face_detector

# Or start all workers
python3 -m scripts.start_worker start

# Check worker status
python3 -m scripts.start_worker status
```

### Step 3: Register & Execute Pipelines

#### Register Pipelines

```bash
# Show available pipeline configurations
python3 -m tools.pipeline_cli_registry show-config

# Register from default config (config_pipeline.json)
python3 -m tools.pipeline_cli_registry register

# Register from custom config file
python3 -m tools.pipeline_cli_registry register --json-config my_pipelines.json

# List registered pipelines
python3 -m tools.pipeline_cli_registry list
```

#### Execute Pipelines

```bash
# Simple pipeline - single face detection
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'

# Complex pipeline - multi-step with parallel processing
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'

# Get detailed pipeline info
python3 -m tools.pipeline_cli_registry info face_processing_pipeline
```

**Expected Results:**
- Simple pipeline: Face detection with bounding boxes (~1-2s)
- Complex pipeline: Face detection + attributes + features (~1-2s with parallel execution)

### Step 4: Production Workflow with Celery Workers

#### Start Workers for Existing Tasks
```bash
# Start all workers for available tasks
python3 -m scripts.start_worker start

# Or start specific task workers
python3 -m scripts.start_worker start --task face_detection
python3 -m scripts.start_worker start --task face_attribute
python3 -m scripts.start_worker start --task face_extractor

# Check worker status
python3 -m scripts.start_worker status
```

#### Execute Pipelines with Workers
```bash
# Execute with Celery workers (distributed processing)
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' --workers

# Execute simple pipeline with workers
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}' --workers
```

#### Monitor & Batch Processing
```bash
# Monitor worker health in real-time
python3 -m scripts.start_worker monitor

# View execution history
python3 -m tools.worker_cli executions --limit 10

# Check worker statistics
python3 -m tools.worker_cli status

# Production workflow simulation - multiple concurrent jobs
for i in {1..5}; do
  python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' --workers &
done

# Monitor concurrent execution
python3 -m scripts.start_worker monitor
```

#### Task Queue Management
```bash
# List all configured tasks
python3 -m tools.task_manager list

# Get task information
python3 -m tools.task_manager info face_detection

# List pipeline tasks with queue information
python3 -m tools.pipeline_cli_registry tasks

# Check specific queue workers
python3 -m tools.worker_cli workers --queue face_detection
```

## 🔧 Development Guide

### Creating Custom Tasks

#### Step 1: Design Task
```python
# Define requirements
- Input format: {"image_path": "/path/to/image.jpg"}
- Output format: {"result": "processed_data"}
- Dependencies: opencv-python, numpy
- Queue: custom_vision
```

#### Step 2: Implement Task
```bash
# Create from template
python3 -m tools.task_manager create my_ai_task --template ml --author "Your Name"
```

Edit `tasks/my_ai_task/task.py`:
```python
from tasks.base.task_base import MLTask

class Task(MLTask):
    def load_model(self):
        # Load your ML model
        return your_model

    def predict(self, preprocessed_input):
        # Run inference
        return self.model.predict(preprocessed_input)

    def preprocess_input(self, input_data):
        # Preprocess input
        return processed_data
```

#### Step 3: Configure Task
Edit `tasks/my_ai_task/task.json`:
```json
{
  "task_id": "my_ai_task",
  "name": "My AI Task",
  "description": "Description of what this task does",
  "requirements": ["tensorflow>=2.0.0"],
  "queue": "ml",
  "priority": 5,
  "timeout": 300
}
```

#### Step 4: Register & Test
```bash
# Register task
python3 -m tools.task_manager register tasks/my_ai_task

# Test task
python3 -m tools.task_manager test my_ai_task '{"input": "test_data"}'
```

### Creating Custom Pipelines

#### Method 1: JSON Configuration (Recommended)

Create or edit `config_pipeline.json`:
```json
{
  "global_settings": {
    "default_timeout": 300,
    "default_retries": 3
  },
  "pipelines": [
    {
      "pipeline_id": "your_custom_pipeline",
      "name": "Your Custom Pipeline",
      "description": "Custom image processing pipeline",
      "enabled": true,
      "steps": [
        {
          "step_id": "step_1",
          "task_id": "face_detection",
          "queue": "face_detection",
          "priority": 7,
          "timeout": 120
        },
        {
          "step_id": "step_2",
          "task_id": "face_attribute",
          "queue": "face_attribute",
          "dependencies": ["step_1"],
          "parallel_group": "group_1"
        }
      ]
    }
  ]
}
```

Register pipeline:
```bash
# Register all pipelines from config
python3 -m tools.pipeline_cli_registry register

# Register from custom config
python3 -m tools.pipeline_cli_registry register --json-config my_config.json
```

#### Method 2: Python Code

```python
from tasks.base.pipeline_base import SequentialPipeline

class MyPipeline(SequentialPipeline):
    def get_tasks(self):
        return ["face_detection", "emotion_recognition"]

    def execute_task(self, task_id, input_data):
        from worker.task_registry import task_registry
        return task_registry.submit_task(task_id, input_data)
```

## 🔧 Command Reference

### Task Management
```bash
# List all tasks
python3 -m tools.task_manager list

# Create new task
python3 -m tools.task_manager create my_task --template ml

# Register task
python3 -m tools.task_manager register tasks/my_task

# Test task
python3 -m tools.task_manager test face_detection '"/path/to/image.jpg"'

# Task info
python3 -m tools.task_manager info face_detection
```

### Worker Management
```bash
# Worker status
python3 -m tools.worker_cli status

# Monitor worker
python3 -m tools.worker_cli monitor

# Execute task
python3 -m tools.worker_cli execute face_detection '{"image_path": "/path/to/image.jpg"}'

# View execution history
python3 -m tools.worker_cli executions --limit 50

# Health check
python3 -m tools.worker_cli health
```

### Pipeline Management
```bash
# Show pipeline configuration
python3 -m tools.pipeline_cli_registry show-config

# Register pipelines
python3 -m tools.pipeline_cli_registry register

# List pipelines
python3 -m tools.pipeline_cli_registry list

# Execute pipeline
python3 -m tools.pipeline_cli_registry execute pipeline_id '{"input": "data"}'

# Pipeline info
python3 -m tools.pipeline_cli_registry info pipeline_id

# List available tasks
python3 -m tools.pipeline_cli_registry tasks
```

## 📊 Monitoring & Management

### Web Interfaces
- **Flower (Celery)**: http://localhost:5555
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

### CLI Monitoring
```bash
# Real-time worker monitor
python3 -m tools.worker_cli monitor

# List all workers
python3 -m tools.worker_cli workers

# Execution history with filters
python3 -m tools.worker_cli executions --status failed
```

### Logs
```bash
# Worker logs
tail -f logs/worker.log

# Celery logs
tail -f logs/celery.log

# System logs
tail -f logs/system.log
```

## ⚙️ Configuration

### Worker Configuration (`config.json`)
```json
{
  "worker": {
    "worker_id": "worker_001",
    "max_concurrent_tasks": 5,
    "active_tasks": ["face_detection", "text_sentiment"],
    "task_configs": {
      "face_detection": {
        "queue": "vision",
        "priority": 7,
        "timeout": 120
      }
    }
  }
}
```

### Environment Variables
```bash
# Database
export MONGODB_HOST=localhost
export MONGODB_PASSWORD=admin123

# Storage
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin123

# Redis
export REDIS_PASSWORD=redis123
```

## 🔐 Production Deployment

### Security
```bash
# Generate secure passwords
export MONGODB_PASSWORD=$(openssl rand -base64 32)
export MINIO_SECRET_KEY=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
```

### Scaling
```bash
# Multiple workers
python3 -m tools.worker_cli start --concurrency 10

# Different queues
python3 -m tools.worker_cli start --queues vision,nlp,ml
```

### Health Checks
```bash
# Automated health check (crontab)
*/5 * * * * cd /path/to/ai-task-worker && python3 -m tools.worker_cli health
```

## 🐛 Troubleshooting

### Common Issues

#### Task Creation/Registration Fails
```bash
# Check templates
python3 -m tools.task_manager list-templates

# Validate task.json
python -m json.tool tasks/your_task/task.json

# Check dependencies
pip install -r tasks/your_task/requirements.txt
```

#### Worker Won't Start
```bash
# Test service connections
python3 -c "import redis; r=redis.Redis(); print('Redis OK:', r.ping())"
python3 -c "import pymongo; c=pymongo.MongoClient(); print('MongoDB OK:', c.admin.command('hello'))"

# Check services
docker-compose ps

# Debug start
python3 -m scripts.start_worker start --loglevel DEBUG
```

#### Pipeline Issues
```bash
# Validate pipeline JSON
python -m json.tool config_pipeline.json

# Register pipelines from config
python3 -m tools.pipeline_cli_registry register

# Test with existing pipelines
python3 -m tools.pipeline_cli_registry list
python3 -m tools.pipeline_cli_registry info face_processing_pipeline

# Test image processing
python3 -c "import cv2; img=cv2.imread('test.jpg'); print('Image OK:', img is not None)"
```

#### Running Existing Tasks Issues
```bash
# Check if tasks are registered
python3 -m tools.task_manager list

# Verify task cache
ls -la task_cache/
python3 -c "import json; print(json.load(open('task_cache/cache_index.json')))"

# Test specific existing tasks (may have Unicode display issues on Windows)
python3 -m tools.task_manager test face_detection '"test.jpg"'
python3 -m tools.task_manager test simple_face_detector '"test.jpg"'

# Check task information
python3 -m tools.task_manager info face_detection
```

#### Known Issues & Status

**✅ Fully Working:**
- Individual task execution (face_detection, simple_face_detector, etc.)
- simple_face_pipeline (single-step face detection)
- Built-in face_processing_pipeline (via demo scripts)
- Task registration and caching
- MinIO/MongoDB/Redis integration
- Logging system
- Worker startup and monitoring

**⚠️ Partial Issues:**
- JSON-configured face_processing_pipeline: Face detection works, but parallel steps (face_attribute, face_extractor) fail due to missing image data passing
- Unicode display issues on Windows console (✓/✗ characters)

**🔧 Workarounds:**
```bash
# Instead of: python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
# Use: python demo_face_processing.py  (This works perfectly!)

# For individual tasks, core functionality works despite display issues
```

#### Image File Issues
```bash
# Check if test image exists
ls -la test.jpg

# Verify image is readable
python3 -c "import cv2; import numpy as np; img=cv2.imread('test.jpg'); print(f'Image shape: {img.shape if img is not None else None}')"

# Use absolute path if relative fails
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{\"image_path\": \"'$(pwd)'/test.jpg\"}'
```

### System Reset
```bash
# Complete reset
python3 -m scripts.start_worker stop
docker-compose down && docker-compose up -d

# Clear cache and re-register
rm -rf task_cache/*
python3 -m tools.task_manager register tasks/
python3 -m tools.pipeline_cli_registry register
python3 -m scripts.start_worker start
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 -m tools.worker_cli start --loglevel DEBUG

# Check logs
tail -f logs/worker.log
```

### System Validation
```bash
# Validate complete system
python3 -c "
import sys
try:
    import cv2, numpy, redis, pymongo, loguru, celery
    print('✓ All dependencies OK')

    import redis; redis.Redis().ping()
    print('✓ Redis connection OK')

    import pymongo; pymongo.MongoClient().admin.command('hello')
    print('✓ MongoDB connection OK')

    import os; os.listdir('task_cache')
    print('✓ Task cache accessible')

    print('System validation: PASSED')
except Exception as e:
    print('System validation: FAILED -', e)
    sys.exit(1)
"
```

## 🏃‍♂️ 30-Second Quick Start

Want to see the system in action immediately? Run these **guaranteed working** commands:

```bash
# 1. ✅ WORKING: Simple face detection pipeline
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'

# 2. ✅ WORKING: Full face processing demo (includes parallel processing)
python demo_face_processing.py

# 3. ✅ WORKING: Individual face detection task
python simple_registration_demo.py
```

**Expected Results:**
- ✅ **simple_face_pipeline**: Face detection with bounding boxes in ~1-2s
- ✅ **demo script**: Complete pipeline with face attributes & features in ~0.12s
- ✅ **registration demo**: Task registration and execution demonstration

**⚠️ Known Issue:** The JSON-configured `face_processing_pipeline` has face detection working but attribute/feature extraction fails due to data passing limitations.

## 📚 Quick Start Scripts

### Windows
```bash
# Automated demo
run_demo.bat

# Quick version
quick_demo.bat
```

### Linux/Mac
```bash
# Make executable and run
chmod +x run_demo.sh
./run_demo.sh

# Background execution
nohup ./run_demo.sh > demo.log 2>&1 &
```

## 🚀 Ready-to-Use Commands Cheat Sheet

### Instant Testing (No Configuration Needed)
```bash
# Test existing tasks
python3 -m tools.task_manager test face_detection '"test.jpg"'
python3 -m tools.task_manager test text_sentiment '"Hello world!"'

# Execute existing pipelines
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'

# List what's available
python3 -m tools.task_manager list
python3 -m tools.pipeline_cli_registry list

# Get detailed information
python3 -m tools.task_manager info face_detection
python3 -m tools.pipeline_cli_registry info face_processing_pipeline
```

### Production Mode (With Workers)
```bash
# Start all workers
python3 -m scripts.start_worker start

# Execute with distributed processing
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' --workers

# Monitor workers
python3 -m scripts.start_worker monitor
```

## 📈 Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Task Creation | < 5s | Template-based generation |
| Task Registration | < 2s | MinIO upload + DB record |
| Worker Startup | < 10s | Service connections + task loading |
| Pipeline Registration | < 1s | JSON parsing + validation |
| Simple Pipeline | 1-2s | Single face detection |
| Complex Pipeline | 1-2s | Parallel task processing |
| Batch Processing (5 images) | 3-5s | Concurrent execution |

## 📚 Detailed Task & Pipeline Reference

### 🎯 Individual Task Examples

#### Face Detection Task (`face_detection`)
```bash
# Test face detection
python3 -m tools.task_manager test face_detection '"test.jpg"'
```
**Expected Output:**
```json
{
  "faces": [
    {
      "bbox": [x, y, width, height],
      "confidence": 0.95
    }
  ],
  "face_count": 1,
  "processing_time": 0.34
}
```

#### Face Attribute Task (`face_attribute`)
```bash
# Test face attributes (requires face detection results)
python3 -m tools.task_manager test face_attribute '{"faces": [{"bbox": [100, 100, 200, 200]}]}'
```
**Expected Output:**
```json
{
  "faces": [
    {
      "bbox": [100, 100, 200, 200],
      "attributes": {
        "age": 25,
        "gender": "male",
        "emotion": "happy",
        "confidence": 0.89
      }
    }
  ]
}
```

#### Face Feature Extractor Task (`face_extractor`)
```bash
# Test feature extraction (requires face detection results)
python3 -m tools.task_manager test face_extractor '{"faces": [{"bbox": [100, 100, 200, 200]}]}'
```
**Expected Output:**
```json
{
  "faces": [
    {
      "bbox": [100, 100, 200, 200],
      "features": [0.1, 0.2, 0.3, ...],
      "feature_dimension": 512
    }
  ]
}
```

#### Text Sentiment Task (`text_sentiment`)
```bash
# Test sentiment analysis
python3 -m tools.task_manager test text_sentiment '"This is amazing!"'
```
**Expected Output:**
```json
{
  "text": "This is amazing!",
  "sentiment": "positive",
  "confidence": 0.92,
  "scores": {
    "positive": 0.92,
    "negative": 0.03,
    "neutral": 0.05
  }
}
```

### 🔗 Pipeline Execution Examples

#### Simple Face Pipeline
```bash
# Execute simple face detection pipeline
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'
```
**Expected Output:**
```json
{
  "pipeline_id": "simple_face_pipeline",
  "status": "completed",
  "execution_time": 1.2,
  "results": {
    "faces": [
      {
        "bbox": [120, 80, 180, 220],
        "confidence": 0.95
      }
    ],
    "face_count": 1
  }
}
```

#### Complete Face Processing Pipeline

**⚠️ Current Status**: The JSON-configured pipeline (face_processing_pipeline from config_pipeline.json) has face detection working, but face_attribute and face_extractor steps fail due to missing image data passing logic.

```bash
# Execute full face processing pipeline (face detection works, attributes/features partially fail)
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
```

**Current Output:**
```json
{
  "pipeline_id": "face_processing_pipeline",
  "status": "completed",
  "execution_time": 1.4,
  "results": {
    "faces": [
      {
        "face_id": 0,
        "bbox": [84, 24, 78, 78],
        "confidence": 1.0,
        "attributes": null,  // ⚠️ Failed - missing image data
        "features": null     // ⚠️ Failed - missing image data
      }
    ],
    "processing_summary": {
      "total_faces_detected": 1,
      "faces_with_attributes": 0,    // ⚠️ Should be 1
      "faces_with_features": 0       // ⚠️ Should be 1
    }
  }
}
```

**✅ Working Alternative - Use Demo Script:**
```bash
# This works perfectly with full parallel processing!
python demo_face_processing.py
```

**Demo Script Output (Working):**
- ✅ Face detection: Found 1 face
- ✅ Face attributes: Completed for face 0
- ✅ Face features: Completed for face 0
- ✅ Parallel execution: 0.12s total time

### 📊 Performance Benchmarks (Using test.jpg)

| Operation | Status | Execution Time | Notes |
|-----------|--------|---------------|--------|
| Individual face_detection | ✅ Working | 0.3-0.5s | OpenCV Haar cascades |
| simple_face_pipeline | ✅ Working | 1.2-1.5s | Face detection via CLI |
| Built-in face_processing_pipeline | ✅ Working | 0.12s | Demo script with parallel execution |
| JSON face_processing_pipeline | ⚠️ Partial | 1.4s | Face detection works, attributes/features fail |
| Individual face_attribute | ⚠️ See notes | 0.2-0.4s | Works in demo, fails in JSON pipeline |
| Individual face_extractor | ⚠️ See notes | 0.4-0.6s | Works in demo, fails in JSON pipeline |

**Legend:**
- ✅ **Working**: Fully functional, recommended for use
- ⚠️ **Partial**: Core functionality works with some limitations
- ❌ **Not Working**: Currently not functional

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our server](https://discord.gg/example)
- 📖 Documentation: [docs.example.com](https://docs.example.com)
- 🐛 Issues: [GitHub Issues](https://github.com/example/ai-task-worker/issues)

---

**Happy AI Task Processing! 🚀**