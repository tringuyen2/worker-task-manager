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
### Demo Step
python3 -m tools.task_manager create simple_face_detector --template simple
python3 -m tools.task_manager register tasks/simple_face_detector
python3 -m tools.task_manager list 
python3 -m tools.task_manager info simple_face_detector  

python3 -m tools.worker_cli start --daemon
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

## 🐛 Troubleshooting

### Common Issues

1. **Worker not starting**
   ```bash
   # Check services
   docker-compose ps
   python3 -m tools.worker_cli health
   ```

2. **Task loading failed**
   ```bash
   # Check task cache
   ls -la task_cache/
   python3 -m tools.task_manager list
   ```

3. **Memory issues**
   ```bash
   # Monitor memory
   python3 -m tools.worker_cli monitor
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 -m tools.worker_cli start --loglevel DEBUG
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