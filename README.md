# AI Task Worker - Complete Setup Guide

## 🏗️ Kiến trúc hệ thống

```
AI Task Worker System
├── MongoDB (Task Registry & Execution History)
├── MinIO (Task Storage - ZIP files)
├── AI Worker (Dynamic Task Loader)
└── Task Registration Tool
```

## 📋 Requirements

```bash
pip install pymongo minio pydantic
```

## 🔧 Setup Instructions

### 1. Tạo file requirements.txt
```txt
pymongo>=4.0.0
minio>=7.1.0
pydantic>=1.10.0
```

### 2. Cài đặt MongoDB
```bash
# Docker
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Hoặc cài đặt local
# Ubuntu: sudo apt install mongodb
# MacOS: brew install mongodb-community
```

### 3. Cài đặt MinIO
```bash
# Docker  
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Access MinIO Console: http://localhost:9001
```

### 4. Tạo config.json
```bash
python3 -c "from config import create_default_config; create_default_config()"
```

Config mặc định sẽ được tạo:
```json
{
  "worker_id": "worker_001",
  "worker_name": "AI Worker Node 1", 
  "active_tasks": [
    "face_detection",
    "text_sentiment"
  ],
  "mongodb": {
    "host": "localhost",
    "port": "27017", 
    "database": "ai_tasks",
    "username": "",
    "password": ""
  },
  "minio": {
    "endpoint": "localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin", 
    "bucket": "ai-tasks",
    "secure": false
  },
  "task_cache_dir": "./task_cache",
  "auto_update": true,
  "max_concurrent_tasks": 5
}
```

## 🚀 Usage Workflows

### Workflow 1: Tạo và đăng ký task mới

#### Bước 1: Tạo template task
```bash
python3 task_register.py create --task-id my_new_task
```

#### Bước 2: Implement task logic
Chỉnh sửa file `tasks/my_new_task/task.py`:

```python
def process(self, input_data: Any) -> Any:
    # Implement your AI logic here
    result = your_ai_processing(input_data)
    return result

def get_requirements(self) -> List[str]:
    return ['opencv-python', 'tensorflow']  # Your dependencies
```

#### Bước 3: Đăng ký task
```bash
python3 task_register.py register --folder tasks/my_new_task
```

### Workflow 2: Cập nhật config và chạy worker

#### Bước 1: Cập nhật config.json
```json
{
  "active_tasks": [
    "face_detection",
    "text_sentiment", 
    "my_new_task"
  ]
}
```

#### Bước 2: Chạy worker
```bash
# Chế độ daemon
python3 ai_worker.py --daemon

# Chế độ single task
python3 ai_worker.py --task my_new_task --input "test data"

# List tasks
python3 ai_worker.py --list
```

### Workflow 3: Quản lý tasks

#### Xem danh sách tasks đã đăng ký
```bash
python3 task_register.py list
```

#### Update task (re-register với version mới)
```bash
python3 task_register.py register --folder tasks/updated_task --task-id existing_task
```

## 📁 Cấu trúc thư mục hoàn chỉnh

```
ai_task_worker/
├── config.py              # Config models & defaults
├── database.py            # MongoDB operations  
├── storage.py             # MinIO operations
├── task_loader.py         # Dynamic task loading
├── ai_worker.py           # Main worker application
├── task_register.py       # Task registration tool
├── config.json            # Worker configuration
├── requirements.txt       # Python dependencies
├── tasks/                 # Task development folder
│   ├── face_detection/
│   │   ├── task.py
│   │   ├── task.json
│   │   └── requirements.txt
│   └── text_sentiment/
│       ├── task.py  
│       ├── task.json
│       └── requirements.txt
└── task_cache/            # Runtime task cache
    └── (extracted tasks)
```

## 🔄 Task Lifecycle

1. **Development**: Tạo task trong `tasks/` folder
2. **Registration**: Đóng gói thành ZIP và upload lên MinIO, lưu metadata vào MongoDB
3. **Configuration**: Thêm task ID vào `active_tasks` trong config.json
4. **Loading**: Worker tự động download và load task khi khởi động
5. **Execution**: Task sẵn sàng xử lý requests
6. **Monitoring**: Execution history được lưu trong MongoDB

## 🧪 Testing

### Test đơn task
```python
# test_task.py
from ai_worker import AIWorker

worker = AIWorker("config.json")
worker.initialize()

result = worker.process_task("face_detection", "path/to/image.jpg")
print(result)
```

### Test với API wrapper
```python
# api_wrapper.py
from flask import Flask, request, jsonify
from ai_worker import AIWorker

app = Flask(__name__)
worker = AIWorker()
worker.initialize()

@app.route('/process/<task_id>', methods=['POST'])
def process_task(task_id):
    input_data = request.json.get('input')
    result = worker.process_task(task_id, input_data)
    return jsonify(result)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    return jsonify(worker.list_tasks())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## 🔧 Advanced Configuration

### Multiple Workers
```json
// config_worker_2.json
{
  "worker_id": "worker_002",
  "worker_name": "AI Worker Node 2",
  "active_tasks": ["object_detection", "speech_recognition"]
}
```

### Production Settings
```json
{
  "mongodb": {
    "host": "mongodb.production.com",
    "port": "27017",
    "database": "ai_tasks_prod",
    "username": "ai_user",
    "password": "secure_password"
  },
  "minio": {
    "endpoint": "s3.amazonaws.com", 
    "access_key": "AWS_ACCESS_KEY",
    "secret_key": "AWS_SECRET_KEY",
    "bucket": "ai-tasks-prod",
    "secure": true
  },
  "max_concurrent_tasks": 10
}
```

## 🐛 Troubleshooting

### Worker không load được task
1. Check MongoDB connection: `python3 -c "from database import *; db = DatabaseManager(load_config()); print(db.connect())"`
2. Check MinIO connection: `python3 -c "from storage import *; s = StorageManager(load_config()); print(s.connect())"`
3. Check task exists: `python3 task_register.py list`

### Task execution lỗi
1. Check logs: `tail -f ai_worker.log`
2. Check task requirements: Dependencies có được cài đủ không?
3. Reload task: `worker.reload_task('task_id')`

### Performance issues
1. Tăng `max_concurrent_tasks`
2. Setup multiple workers
3. Cache tasks locally trong production

## 🎯 Key Benefits

1. **Modular**: Dễ dàng thêm/xóa tasks
2. **Scalable**: Multiple workers, load balancing
3. **Persistent**: Task code stored in MinIO, metadata in MongoDB  
4. **Flexible**: Config-driven task activation
5. **Robust**: Error handling, execution history, logging
6. **Production-ready**: Daemon mode, graceful shutdown, monitoring

Hệ thống này cho phép bạn dễ dàng deploy và quản lý hàng trăm AI tasks khác nhau chỉ bằng cách cập nhật config và restart worker!