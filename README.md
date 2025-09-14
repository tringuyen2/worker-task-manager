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

## 🎯 Complete Demo Workflow

### Prerequisites
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

### Step 4: Monitor & Batch Processing

```bash
# Monitor worker health
python3 -m scripts.start_worker monitor

# View execution history
python3 -m tools.worker_cli executions --limit 10

# Run demo scripts
python demo_face_processing.py
python simple_registration_demo.py
python json_pipeline_demo.py

# Production workflow simulation - multiple concurrent jobs
for i in {1..5}; do
  python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' &
done
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

# Register specific pipeline
python3 -m tools.pipeline_cli_registry register --pipeline your_pipeline

# Test image processing
python3 -c "import cv2; img=cv2.imread('test.jpg'); print('Image OK:', img is not None)"
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

## 📚 Example Tasks

### Face Detection (`face_detection`)
- OpenCV Haar Cascades
- Input: Image path or numpy array
- Output: Bounding boxes và confidence scores

### Text Sentiment (`text_sentiment`)
- Rule-based sentiment analysis
- Input: Text string
- Output: Sentiment (positive/negative/neutral) với confidence

### Testing Examples
```bash
# Test face detection
python3 -m tools.task_manager test face_detection '"test_image.jpg"'

# Test sentiment analysis
python3 -m tools.task_manager test text_sentiment '"This is amazing!"'
```

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