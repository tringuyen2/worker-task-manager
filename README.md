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

## ⚡ Cài Đặt Nhanh

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai-task-worker
```

### 2. Khởi Động Services

```bash
# Start MongoDB, MinIO, Redis
docker-compose up -d

# Check services
docker-compose ps
```

### 3. Cài Đặt Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Khởi Tạo Hệ Thống

```bash
python3 scripts/init_system.py
```

### 5. Khởi Động Worker

```bash
# Method 1: Use script
./start_worker.sh

# Method 2: Manual
python3 -m tools.worker_cli start --daemon
```

## 🔧 Sử Dụng

### Quản Lý Tasks

```bash
# List all tasks
python3 -m tools.task_manager list

# Create new task
python3 -m tools.task_manager create my_new_task --template ml

# Register task
python3 -m tools.task_manager register tasks/my_new_task

# Test task
python3 -m tools.task_manager test face_detection '"/path/to/image.jpg"'

# Task info
python3 -m tools.task_manager info face_detection
```

### Quản Lý Workers

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

### API Usage (Python)

```python
from worker.task_registry import task_registry

# Submit task
execution_id = task_registry.submit_task(
    "face_detection", 
    {"image_path": "/path/to/image.jpg"}
)

# Check result
from core.database.operations import db_ops
record = db_ops.get_execution_record(execution_id)
print(record.status, record.output_data)
```

## 📝 Tạo Task Mới

### 1. Create Task Template

```bash
python3 -m tools.task_manager create my_ai_task --template ml --author "Your Name"
```

### 2. Implement Task Logic

Chỉnh sửa `tasks/my_ai_task/task.py`:

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

### 3. Configure Task

Chỉnh sửa `tasks/my_ai_task/task.json`:

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

### 4. Register Task

```bash
python3 -m tools.task_manager register tasks/my_ai_task
```

## 🔄 Pipeline System

### Sequential Pipeline

```python
from tasks.base.pipeline_base import SequentialPipeline

class MyPipeline(SequentialPipeline):
    def get_tasks(self):
        return ["face_detection", "emotion_recognition"]
    
    def execute_task(self, task_id, input_data):
        from worker.task_registry import task_registry
        return task_registry.submit_task(task_id, input_data)
```

### Parallel Pipeline

```python
from tasks.base.pipeline_base import ParallelPipeline

class MyParallelPipeline(ParallelPipeline):
    def get_tasks(self):
        return ["face_detection", "object_detection", "scene_classification"]
    
    def execute_task(self, task_id, input_data):
        # Execute task
        pass
    
    def process_parallel_results(self, task_results, input_data):
        # Combine results
        return combined_result
```
## 🎯 Complete Step-by-Step Demo

### Prerequisites
- Ensure all services are running: MongoDB, MinIO, Redis
- Python dependencies installed
- Test image available (`test.jpg`)

### Step 1: Create a New Task

```bash
# Create a new task from template
python3 -m tools.task_manager create simple_face_detector --template simple

# Verify the task structure
ls -la tasks/simple_face_detector/
```

**What you'll see:**
- `task.py` - Main task implementation
- `task.json` - Task configuration
- `requirements.txt` - Task dependencies

### Step 2: Register the Task

```bash
# Register the task in the system
python3 -m tools.task_manager register tasks/simple_face_detector

# List all available tasks
python3 -m tools.task_manager list

# Get detailed task information
python3 -m tools.task_manager info simple_face_detector
```

**Expected output:**
- Task successfully registered
- Task appears in the task list
- Configuration details displayed

### Step 3: Start Celery Workers

```bash
# Start worker daemon for specific task
python3 -m scripts.start_worker start --task simple_face_detector

# Or start all workers
python3 -m scripts.start_worker start

# Check worker status
python3 -m scripts.start_worker status
```

**What happens:**
- Celery worker processes start
- Workers connect to Redis broker
- Tasks are ready to receive jobs

### Step 4: Register Pipelines

```bash
# Show available pipeline configurations
python3 -m tools.pipeline_cli_registry show-config

# Register pipelines from JSON configuration
python3 -m tools.pipeline_cli_registry register

# List registered pipelines
python3 -m tools.pipeline_cli_registry list
```

**Pipeline types available:**
- `simple_face_pipeline` - Single face detection step
- `face_processing_pipeline` - Multi-step with parallel execution
- Custom pipelines from `config_pipeline.json`

### Step 5: Process Image - Simple Pipeline

```bash
# Execute simple face detection pipeline
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'
```

**Expected results:**
```json
{
  "pipeline_id": "simple_face_pipeline",
  "execution_id": "exec_12345",
  "results": {
    "faces": [
      {
        "bbox": [x, y, width, height],
        "confidence": 0.95
      }
    ]
  },
  "execution_time": 1.2,
  "status": "completed"
}
```

### Step 6: Process Image - Complex Pipeline

```bash
# Execute complex face processing pipeline
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
```

**Processing stages:**
1. **Stage 1 (Sequential)**: Face detection
2. **Stage 2 (Parallel)**: Face attributes + Feature extraction
3. **Final Result**: Combined face data with attributes and features

**Expected results:**
```json
{
  "pipeline_id": "face_processing_pipeline",
  "results": {
    "faces": [
      {
        "bbox": [x, y, width, height],
        "confidence": 0.95,
        "attributes": {
          "age": 25,
          "gender": "male",
          "emotion": "happy"
        },
        "features": [0.1, 0.2, ...],
        "feature_dimension": 512
      }
    ]
  },
  "execution_time": 1.8,
  "parallel_execution": true
}
```

### Step 7: Monitor Workers and Tasks

```bash
# Monitor worker health
python3 -m scripts.start_worker monitor

# View execution history
python3 -m tools.worker_cli executions --limit 10

# Check worker status
python3 -m tools.worker_cli status

# Test specific task directly
python3 -m tools.task_manager test simple_face_detector '"test.jpg"'
```

### Step 8: Advanced Pipeline Operations

```bash
# Get detailed pipeline information
python3 -m tools.pipeline_cli_registry info face_processing_pipeline

# List all available tasks with configurations
python3 -m tools.pipeline_cli_registry tasks

# Execute with custom parameters
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{
  "image_path": "test.jpg",
  "min_face_size": 50,
  "confidence_threshold": 0.8
}'
```

### Step 9: Batch Processing Demo

```bash
# Run the complete demo script
python demo_face_processing.py

# Run simple registration demo
python simple_registration_demo.py

# Run JSON pipeline demo
python json_pipeline_demo.py
```

**What these demos show:**
- Complete system workflow
- Pipeline registration process
- Task execution with timing
- Error handling and recovery

### Step 10: Production Workflow Simulation

```bash
# Start multiple workers for different queues
python3 -m scripts.start_worker start --task face_detection
python3 -m scripts.start_worker start --task face_attribute
python3 -m scripts.start_worker start --task face_extractor

# Submit multiple jobs simultaneously
for i in {1..5}; do
  python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}' &
done

# Monitor concurrent execution
python3 -m scripts.start_worker monitor
```

## 🔄 Custom Task Development Workflow

### Step 1: Design Your Task
```python
# Define task requirements
- Input format: {"image_path": "/path/to/image.jpg"}
- Output format: {"result": "processed_data"}
- Dependencies: opencv-python, numpy
- Queue: custom_vision
```

### Step 2: Implement Task Logic
```python
# Edit tasks/your_task/task.py
from tasks.base.task_base import BaseTask

class Task(BaseTask):
    def execute(self, input_data):
        # Your task logic here
        return {"result": "processed_data"}
```

### Step 3: Configure and Register
```bash
# Update tasks/your_task/task.json
# Register the task
python3 -m tools.task_manager register tasks/your_task

# Test the task
python3 -m tools.task_manager test your_task '{"input": "test_data"}'
```

### Step 4: Create Pipeline Integration
```json
// Add to config_pipeline.json
{
  "pipeline_id": "your_custom_pipeline",
  "steps": [
    {
      "task_id": "your_task",
      "queue": "custom_vision"
    }
  ]
}
```

### Step 5: Deploy and Monitor
```bash
# Start worker for your task
python3 -m scripts.start_worker start --task your_task

# Execute pipeline
python3 -m tools.pipeline_cli_registry execute your_custom_pipeline '{"input": "data"}'

# Monitor execution
python3 -m scripts.start_worker monitor
```

## 🎬 Quick Demo Scripts

### Windows Quick Start
```bash
# Run automated demo
run_demo.bat

# Quick version (no pauses)
quick_demo.bat
```

### Linux/Mac Quick Start
```bash
# Make executable and run
chmod +x run_demo.sh
./run_demo.sh

# Background execution
nohup ./run_demo.sh > demo.log 2>&1 &
```

## 📋 Demo Summary & Key Takeaways

### What This Demo Demonstrates

1. **Complete Development Lifecycle**
   - Task creation from templates
   - Configuration and registration
   - Worker deployment and scaling
   - Pipeline orchestration
   - Production monitoring

2. **Key System Capabilities**
   - **Dynamic Task Loading**: Tasks loaded from MinIO storage
   - **Parallel Processing**: Multiple tasks execute simultaneously
   - **Queue Management**: Different task types use dedicated queues
   - **JSON Configuration**: Pipelines defined without code changes
   - **Health Monitoring**: Real-time worker and task status
   - **Fault Tolerance**: Automatic retry and error handling

3. **Production-Ready Features**
   - Distributed worker architecture
   - Celery-based task queue system
   - MongoDB for execution tracking
   - MinIO for scalable file storage
   - Redis for message brokering
   - CLI tools for management and monitoring

### Expected Demo Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Task Creation | < 5s | Template-based generation |
| Task Registration | < 2s | MinIO upload + DB record |
| Worker Startup | < 10s | Service connections + task loading |
| Pipeline Registration | < 1s | JSON parsing + validation |
| Simple Pipeline Execution | 1-2s | Single face detection |
| Complex Pipeline Execution | 1-2s | Parallel task processing |
| Batch Processing (5 images) | 3-5s | Concurrent pipeline execution |

### Demo Success Criteria

✅ **Tasks**: Created, registered, and executable
✅ **Workers**: Started and responsive to task queues
✅ **Pipelines**: Registered and processing images correctly
✅ **Monitoring**: Real-time status and execution history
✅ **Performance**: Sub-2 second processing times
✅ **Scalability**: Multiple concurrent executions

### Next Steps After Demo

1. **Development**: Create custom tasks for your use case
2. **Configuration**: Modify `config_pipeline.json` for your workflows
3. **Scaling**: Deploy multiple workers across different machines
4. **Integration**: Use Python API for programmatic access
5. **Production**: Set up monitoring, logging, and health checks

## 📊 Monitoring

### Web Interfaces

- **Flower (Celery)**: http://localhost:5555
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

### CLI Monitoring

```bash
# Real-time worker monitor
python3 -m tools.worker_cli monitor

# List all workers
python3 -m tools.worker_cli workers

# Execution history
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
# Automated health check
*/5 * * * * cd /path/to/ai-task-worker && python3 -m tools.worker_cli health
```

## 🐛 Troubleshooting & Demo Issues

### Common Demo Issues

1. **Task Creation Fails**
   ```bash
   # Check if template exists
   python3 -m tools.task_manager list-templates

   # Verify directory permissions
   ls -la tasks/

   # Create with different template
   python3 -m tools.task_manager create test_task --template basic
   ```

2. **Task Registration Fails**
   ```bash
   # Check task structure
   ls -la tasks/your_task/

   # Validate task.json format
   python -m json.tool tasks/your_task/task.json

   # Check dependencies
   pip install -r tasks/your_task/requirements.txt

   # Register with verbose output
   python3 -m tools.task_manager register tasks/your_task --verbose
   ```

3. **Worker Won't Start**
   ```bash
   # Check Redis connection
   python3 -c "import redis; r=redis.Redis(); print('Redis OK:', r.ping())"

   # Check MongoDB connection
   python3 -c "import pymongo; c=pymongo.MongoClient(); print('MongoDB OK:', c.admin.command('hello'))"

   # Check services status
   docker-compose ps

   # Start specific worker with debug
   python3 -m scripts.start_worker start --task your_task --loglevel DEBUG
   ```

4. **Pipeline Registration Issues**
   ```bash
   # Validate JSON configuration
   python -m json.tool config_pipeline.json

   # Check pipeline syntax
   python3 -m tools.pipeline_cli_registry validate

   # Register single pipeline
   python3 -m tools.pipeline_cli_registry register --pipeline face_processing_pipeline
   ```

5. **Image Processing Fails**
   ```bash
   # Check image file exists and is readable
   python3 -c "import cv2; img=cv2.imread('test.jpg'); print('Image OK:', img is not None)"

   # Check image path format
   python3 -c "import os; print('Absolute path:', os.path.abspath('test.jpg'))"

   # Test with different image
   python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "path/to/other/image.jpg"}'
   ```

6. **Pipeline Execution Hangs**
   ```bash
   # Check worker queues
   python3 -m scripts.start_worker status

   # Check active tasks
   python3 -c "import celery; app=celery.Celery('worker'); print(app.control.active())"

   # Kill stuck tasks
   python3 -m scripts.start_worker stop
   python3 -m scripts.start_worker start
   ```

### Performance Issues

1. **Slow Execution**
   ```bash
   # Monitor CPU and memory usage
   python3 -m scripts.start_worker monitor

   # Reduce concurrent tasks
   # Edit config.json: "max_concurrent_tasks": 2

   # Use lighter task queues
   python3 -m scripts.start_worker start --task simple_face_detector
   ```

2. **Memory Leaks**
   ```bash
   # Restart workers periodically
   python3 -m scripts.start_worker restart

   # Monitor memory usage
   python3 -c "import psutil; print('Memory:', psutil.virtual_memory().percent, '%')"
   ```

### Environment Issues

1. **Missing Dependencies**
   ```bash
   # Install all requirements
   pip install -r requirements.txt

   # Check specific task requirements
   pip install -r tasks/face_detection/requirements.txt

   # Verify OpenCV installation
   python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
   ```

2. **Service Connection Issues**
   ```bash
   # Test MongoDB connection
   python3 -c "
   from core.database.connection import get_database_connection
   try:
       db = get_database_connection()
       print('MongoDB: Connected')
   except Exception as e:
       print('MongoDB Error:', e)
   "

   # Test MinIO connection
   python3 -c "
   from core.storage.minio_client import get_minio_client
   try:
       client = get_minio_client()
       print('MinIO: Connected')
   except Exception as e:
       print('MinIO Error:', e)
   "

   # Test Redis connection
   python3 -c "
   import redis
   from core.config.config_manager import get_redis_config
   try:
       config = get_redis_config()
       r = redis.Redis(**config)
       r.ping()
       print('Redis: Connected')
   except Exception as e:
       print('Redis Error:', e)
   "
   ```

### Debug Mode & Logging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 -m tools.worker_cli start --loglevel DEBUG

# View logs in real-time
tail -f logs/worker.log
tail -f logs/celery.log

# Check specific task logs
python3 -m tools.task_manager test your_task '{"input": "data"}' --verbose
```

### Reset System State

```bash
# Complete system reset
python3 -m scripts.start_worker stop
docker-compose down
docker-compose up -d

# Clear task cache
rm -rf task_cache/*

# Re-register all tasks
python3 -m tools.task_manager register tasks/

# Re-register pipelines
python3 -m tools.pipeline_cli_registry register

# Restart workers
python3 -m scripts.start_worker start
```

### Validation Commands

```bash
# Validate complete system
python3 -c "
import sys
try:
    # Test imports
    import cv2, numpy, redis, pymongo, loguru, celery
    print('✓ All dependencies imported')

    # Test services
    import redis; redis.Redis().ping()
    print('✓ Redis connection OK')

    import pymongo; pymongo.MongoClient().admin.command('hello')
    print('✓ MongoDB connection OK')

    # Test task cache
    import os; os.listdir('task_cache')
    print('✓ Task cache accessible')

    print('System validation: PASSED')
except Exception as e:
    print('System validation: FAILED -', e)
    sys.exit(1)
"
```

## 📚 Examples

### Example Tasks Included

1. **Face Detection** (`face_detection`)
   - OpenCV Haar Cascades
   - Input: Image path or numpy array
   - Output: Bounding boxes và confidence scores

2. **Text Sentiment** (`text_sentiment`)
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