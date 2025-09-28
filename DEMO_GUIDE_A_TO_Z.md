# Worker Task Manager Demo Guide A-Z

A complete step-by-step guide to run the Worker Task Manager demo from setup to execution.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Service Configuration](#service-configuration)
4. [Task Registration](#task-registration)
5. [Pipeline Configuration](#pipeline-configuration)
6. [Demo Execution](#demo-execution)
7. [Production Workflow](#production-workflow)
8. [Monitoring & Debugging](#monitoring--debugging)
9. [Advanced Usage](#advanced-usage)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux/macOS/Windows with WSL
- **Python**: 3.8 or higher
- **Docker**: Latest version with Docker Compose
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space

### Required Tools
```bash
# Check prerequisites
python3 --version        # Should be 3.8+
docker --version         # Should be 20.10+
docker compose version   # Should be 2.0+
git --version           # Any recent version
```

---

## Environment Setup

### Step A1: Clone Repository
```bash
# Clone the repository
git clone <repository-url>
cd worker-task-manager

# Verify directory structure
ls -la
# Should see: tasks/, pipeline/, config.json, docker-compose.yaml, etc.
```

### Step A2: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Verify activation
which python  # Should point to venv/bin/python
```

### Step A3: Install Dependencies
```bash
# Install Python dependencies
./venv/bin/pip install -r requirements.txt

# Install additional required packages
./venv/bin/pip install opencv-python numpy celery redis loguru

# Verify installation
./venv/bin/pip list | grep -E "(opencv|celery|redis)"
```

---

## Service Configuration

### Step B1: Start Docker Services
```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Expected output:
# ai_worker_mongodb   Up      27017->27017/tcp
# ai_worker_redis     Up      6379->6379/tcp
# ai_worker_minio     Up      9000-9001->9000-9001/tcp
# ai_worker_flower    Up      5555->5555/tcp
```

### Step B2: Fix MinIO Configuration
```bash
# Check current config
cat config.json | grep -A 6 '"minio"'

# Update MinIO secret key if needed
# Edit config.json and change:
# "secret_key": "minioadmin"  →  "secret_key": "minioadmin123"
```

**Edit config.json**:
```json
{
  "minio": {
    "endpoint": "localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin123",
    "bucket": "ai-tasks",
    "secure": false
  }
}
```

### Step B3: Verify Service Connectivity
```bash
# Test MongoDB connection
docker compose logs mongodb | tail -5

# Test MinIO connection
curl -I http://localhost:9000
# Should return HTTP/1.1 403 Forbidden (expected)

# Test Redis connection
docker compose logs redis | tail -5
```

---

## Task Registration

### Step C1: Check Available Tasks
```bash
# List available task directories
find tasks/ -name "task.py" -o -name "task.json"

# Expected output:
# tasks/examples/face_detection/task.py
# tasks/examples/face_detection/task.json
# tasks/examples/face_attribute/task.py
# tasks/examples/face_attribute/task.json
# tasks/examples/face_extractor/task.py
# tasks/examples/face_extractor/task.json
```

### Step C2: Register Face Detection Task
```bash
# Register face detection task
./venv/bin/python -m tools.task_manager register tasks/examples/face_detection

# Expected output:
# ✓ Task validation passed
# ✓ Task registered successfully: face_detection
# ✓ Worker configuration updated
```

### Step C3: Register Face Attribute Task
```bash
# Register face attribute task
./venv/bin/python -m tools.task_manager register tasks/examples/face_attribute

# Expected output:
# ✓ Task validation passed
# ✓ Task registered successfully: face_attribute
# ✓ Worker configuration updated
```

### Step C4: Register Face Extractor Task
```bash
# Register face extractor task
./venv/bin/python -m tools.task_manager register tasks/examples/face_extractor

# Expected output:
# ✓ Task validation passed
# ✓ Task registered successfully: face_extractor
# ✓ Worker configuration updated
```

### Step C5: Verify Task Registration
```bash
# List all registered tasks
./venv/bin/python -m tools.task_manager list

# Expected output: Table showing 3 registered tasks
# face_detection | Face Detection | 1.0.0 | Active
# face_attribute | Face Attribute Analysis | 1.0.1 | Active
# face_extractor | Face Feature Extractor | 1.0.1 | Active
```

---

## Pipeline Configuration

### Step D1: Register Built-in Pipeline
```bash
# Register the built-in face processing pipeline
./venv/bin/python -m tools.pipeline_cli_registry register

# Expected output:
# ✓ Registered pipeline: face_processing_pipeline
# ✓ Registered built-in pipelines
```

### Step D2: Check Pipeline Status
```bash
# List registered pipelines
./venv/bin/python -m tools.pipeline_cli_registry list

# Expected output:
# face_processing_pipeline | Face Processing Pipeline | 0 steps
```

### Step D3: Get Pipeline Information
```bash
# Get detailed pipeline info
./venv/bin/python -m tools.pipeline_cli_registry info face_processing_pipeline

# Expected output: JSON with pipeline details including stages and capabilities
```

### Step D4: Register Custom Demo Pipeline (Optional)
```bash
# Register demo pipeline with unique IDs (if you want to test ID-based mapping)
./venv/bin/python -m tools.pipeline_cli_registry register --json-config demo_pipeline_config.json

# Expected output:
# ✓ Pipeline registered: demo_face_processing_pipeline
# ✓ Data flow mapping configured
```

---

## Demo Execution

### Step E1: Prepare Test Image
```bash
# Verify test image exists
ls -la test.jpg

# If missing, you can use any image file:
# cp /path/to/your/image.jpg test.jpg
```

### Step E2: Test Individual Task
```bash
# Test face detection task
./venv/bin/python -m tools.task_manager test face_detection '"test.jpg"'

# Expected output:
# ✓ Task execution completed
# Result: {"faces": [{"face_id": 0, "bbox": [...], ...}], ...}
```

### Step E3: Execute Complete Pipeline
```bash
# Execute the complete face processing pipeline
./venv/bin/python -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'

# Expected output:
# ✓ Pipeline execution completed successfully
# Processed 1 faces
# Execution Time: ~1.2s
# Status: completed
# Full results with face detection, attributes, and features
```

### Step E4: Verify Results
The pipeline should return:
- **Face Detection**: Bounding boxes, confidence scores
- **Face Attributes**: Age estimation, gender, emotion analysis
- **Face Features**: 128-dimension feature vectors, landmarks

Example output structure:
```json
{
  "faces": [
    {
      "face_id": 0,
      "bbox": [84, 24, 78, 78],
      "confidence": 1.0,
      "attributes": {
        "age": {"estimated_age": 35, "confidence": 0.8},
        "gender": {"predicted_gender": "male", "confidence": 0.7},
        "emotion": {"dominant_emotion": "happy", "confidence": 0.6}
      },
      "features": {
        "feature_vector": [0.7902, 0.7845, ...],
        "landmarks": [[0, 62], [4, 65], ...]
      }
    }
  ]
}
```

---

## Production Workflow

### Step F1: Start Celery Workers
```bash
# Start workers for all tasks
./venv/bin/python -m scripts.start_worker start

# OR start specific workers
./venv/bin/python -m scripts.start_worker start --task face_detection
./venv/bin/python -m scripts.start_worker start --task face_attribute
./venv/bin/python -m scripts.start_worker start --task face_extractor
```

### Step F2: Execute with Workers
```bash
# Execute pipeline using workers
./venv/bin/python -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' --workers

# This will distribute tasks across workers for better performance
```

### Step F3: Monitor Workers
```bash
# Check worker status
./venv/bin/python -m scripts.start_worker status

# Monitor worker activity
./venv/bin/python -m scripts.start_worker monitor

# View execution history
./venv/bin/python -m tools.worker_cli executions --limit 10
```

---

## Monitoring & Debugging

### Step G1: Web Interfaces
```bash
# Access web monitoring interfaces:

# Flower (Celery monitoring)
open http://localhost:5555

# MinIO Console
open http://localhost:9001
# Login: minioadmin / minioadmin123
```

### Step G2: Check Logs
```bash
# View service logs
docker compose logs mongodb
docker compose logs redis
docker compose logs minio

# View application logs
./venv/bin/python -m tools.worker_cli logs face_detection
```

### Step G3: System Status
```bash
# Check task registration status
./venv/bin/python -m tools.task_manager list

# Check pipeline status
./venv/bin/python -m tools.pipeline_cli_registry list

# Check worker status
./venv/bin/python -m scripts.start_worker status
```

---

## Advanced Usage

### Step H1: Batch Processing
```bash
# Process multiple images
for img in *.jpg; do
  ./venv/bin/python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"$img\"}"
done
```

### Step H2: Custom Pipeline Creation
```bash
# Edit pipeline configuration
vim config_pipeline.json

# Register updated pipelines
./venv/bin/python -m tools.pipeline_cli_registry register
```

### Step H3: Performance Monitoring
```bash
# Monitor execution performance
./venv/bin/python -m tools.worker_cli executions --status completed

# Check failed executions
./venv/bin/python -m tools.worker_cli executions --status failed
```

### Step H4: Scaling Workers
```bash
# Start multiple workers for same task
./venv/bin/python -m scripts.start_worker start --task face_detection --concurrency 3
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Task Registration Fails
**Error**: `Failed to upload task package`
**Solution**:
```bash
# Check MinIO configuration
cat config.json | grep -A 6 '"minio"'

# Update secret key
# Change "minioadmin" to "minioadmin123" in config.json

# Restart MinIO
docker compose restart minio
```

#### Issue 2: Module Not Found
**Error**: `No module named 'cv2'` or `No module named 'celery'`
**Solution**:
```bash
# Install missing dependencies
./venv/bin/pip install opencv-python numpy celery redis loguru

# Verify installation
./venv/bin/pip list | grep opencv
```

#### Issue 3: Services Not Running
**Error**: Connection refused errors
**Solution**:
```bash
# Check service status
docker compose ps

# Restart services
docker compose down
docker compose up -d

# Check logs
docker compose logs
```

#### Issue 4: Pipeline Execution Fails
**Error**: Task execution errors
**Solution**:
```bash
# Test individual tasks first
./venv/bin/python -m tools.task_manager test face_detection '"test.jpg"'

# Check task logs
./venv/bin/python -m tools.worker_cli logs face_detection

# Verify image path is correct
ls -la test.jpg
```

#### Issue 5: Command Line Parsing
**Error**: `Missing argument 'PIPELINE_ID'`
**Solution**:
```bash
# Ensure command is on single line
./venv/bin/python -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'

# Use quotes correctly around JSON
```

---

## Demo Scripts

### Quick Demo Scripts
```bash
# Run comprehensive information script
python3 get_info.py

# Run step-by-step demo
python3 demo_step_by_step.py

# Run registration guide
python3 register_demo_tasks.py

# Run next steps guide
python3 next_steps_guide.py
```

---

## Verification Checklist

### ✅ Pre-Demo Checklist
- [ ] Docker services running (`docker compose ps`)
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] MinIO configuration updated
- [ ] Test image available

### ✅ Task Registration Checklist
- [ ] face_detection task registered
- [ ] face_attribute task registered
- [ ] face_extractor task registered
- [ ] All tasks show as "Active" in list

### ✅ Pipeline Registration Checklist
- [ ] Built-in pipeline registered (`./venv/bin/python -m tools.pipeline_cli_registry register`)
- [ ] face_processing_pipeline appears in list
- [ ] Pipeline info shows stages and capabilities
- [ ] (Optional) Demo pipeline with unique IDs registered

### ✅ Execution Checklist
- [ ] Individual task test passes
- [ ] Pipeline execution completes successfully
- [ ] Results include face detection data
- [ ] Results include face attributes
- [ ] Results include feature vectors
- [ ] Execution time is reasonable (~1-2s)

### ✅ Production Checklist
- [ ] Workers can be started
- [ ] Worker-based execution works
- [ ] Monitoring interfaces accessible
- [ ] Logs are available and readable

---

## Success Metrics

### Expected Performance
- **Face Detection**: ~0.3-0.5 seconds
- **Face Attributes**: ~0.2-0.4 seconds (parallel)
- **Face Features**: ~0.4-0.6 seconds (parallel)
- **Total Pipeline**: ~0.8-1.2 seconds
- **Parallel Speedup**: ~2x vs sequential

### Expected Results
- **Face Detection**: Bounding boxes with 90%+ confidence
- **Age Estimation**: Within 5-10 years of apparent age
- **Gender Detection**: 70%+ confidence
- **Emotion Analysis**: Multi-emotion scores
- **Feature Vectors**: 128-dimensional normalized vectors
- **Landmarks**: 68-point facial landmarks

---

## Conclusion

This guide provides a complete A-Z walkthrough for running the Worker Task Manager demo. Following these steps should result in a fully functional system capable of:

1. **Task Management**: Register, validate, and execute AI tasks
2. **Pipeline Orchestration**: Execute complex workflows with dependencies
3. **Parallel Processing**: Run multiple tasks simultaneously
4. **Production Deployment**: Scale with distributed workers
5. **Monitoring**: Track performance and debug issues

For additional help, refer to the troubleshooting section or run the demo scripts for automated guidance.

**Total Setup Time**: ~15-30 minutes
**Demo Execution Time**: ~2-5 minutes
**Expected Success Rate**: 95%+ with proper setup

🎉 **Success!** You now have a fully functional AI task management and pipeline orchestration system!