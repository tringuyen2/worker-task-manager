# Worker Task Manager v2 - Demo Guide

## Quick Start (5 Minutes)

Run the automated demo:
```bash
# Windows
run_demo.bat

# Linux/Mac
chmod +x run_demo.sh
./run_demo.sh

# Quick version (no pauses)
quick_demo.bat
```

## Manual Step-by-Step Demo

### Step 1: Show Project Overview
```bash
# Show main files
dir
```

Expected files:
- `config.json` - Main system configuration
- `config_pipeline.json` - Pipeline definitions
- `test.jpg` - Sample image for testing

### Step 2: View Pipeline Configuration
```bash
python -m tools.pipeline_cli_registry show-config
```

**What you'll see:**
- Global settings (timeouts, retries, etc.)
- 3 pipeline definitions:
  - `face_processing_pipeline` (3 steps with parallel execution)
  - `simple_face_pipeline` (1 step, face detection only)
  - `text_analysis_pipeline` (disabled)

### Step 3: Register Pipelines
```bash
python -m tools.pipeline_cli_registry register
```

**Expected output:**
```
Registering all pipelines (built-in + JSON)...
Total registered: 3 pipelines
  • face_processing_pipeline
  • simple_face_pipeline
```

### Step 4: View Available Tasks
```bash
python -m tools.pipeline_cli_registry tasks
```

**What you'll see:**
- Task configurations with queues, priorities, timeouts
- face_detection, face_attribute, face_extractor tasks

### Step 5: Execute Simple Pipeline
```bash
python -m tools.pipeline_cli_registry execute simple_face_pipeline "{\"image_path\": \"test.jpg\"}"
```

**Expected results:**
- Pipeline executes face detection only
- Finds 1 face with bounding box
- Execution time ~1-2 seconds

### Step 6: Execute Complex Pipeline
```bash
python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"test.jpg\"}"
```

**Expected results:**
- Stage 1: Face detection (sequential)
- Stage 2: face_attribute + face_extractor (parallel)
- Final result: Face with both attributes and features
- Execution time ~1-2 seconds

### Step 7: Get Pipeline Details
```bash
python -m tools.pipeline_cli_registry info face_processing_pipeline
```

**What you'll see:**
- Detailed pipeline information
- Step definitions with dependencies
- Input/output format specifications

### Step 8: View Worker Commands
```bash
python -m scripts.start_worker --help
```

**Available commands:**
- `start` - Start workers
- `stop` - Stop workers
- `status` - Check worker status
- `monitor` - Monitor worker health

### Step 9: Check Worker Status
```bash
python -m scripts.start_worker status
```

**What you'll see:**
- List of running Celery processes (if any)
- Shows worker process IDs and command lines

### Step 10: Run Complete Demo
```bash
python demo_face_processing.py
```

**What this shows:**
- Pipeline registration process
- Task registration with queues
- Pipeline execution with timing
- Complete system overview

## Key Demo Points to Highlight

### 1. JSON Configuration
- **No code changes needed** to add new pipelines
- Edit `config_pipeline.json` to define new pipelines
- Automatic validation and registration

### 2. Parallel Execution
- `face_attribute` and `face_extractor` run simultaneously
- Dependencies: Both wait for `face_detection` to complete
- Managed by `parallel_group` setting

### 3. Task Queues
- Each task type has its own queue
- `face_detection` → `face_detection` queue
- `face_attribute` → `face_attribute` queue
- `face_extractor` → `face_extractor` queue

### 4. Worker Management
- Start individual workers: `python -m scripts.start_worker start --task face_detection`
- Start all workers: `python -m scripts.start_worker start`
- Monitor workers: `python -m scripts.start_worker monitor`

### 5. CLI Tools
- `show-config` - View JSON configuration
- `register` - Register pipelines from JSON
- `list` - Show registered pipelines
- `execute` - Run pipelines
- `info` - Get pipeline details

## Expected Performance

- **Pipeline Registration**: < 1 second
- **Simple Pipeline**: 1-2 seconds (face detection only)
- **Complex Pipeline**: 1-2 seconds (parallel execution)
- **Memory Usage**: ~100-200MB per task
- **Scalability**: 10+ concurrent tasks per worker

## Demo Scenarios

### Scenario 1: Business User
"I want to add a new image processing pipeline without touching code"
1. Edit `config_pipeline.json`
2. Add new pipeline definition
3. Run `register` command
4. Pipeline is ready to use

### Scenario 2: DevOps Engineer
"I need to scale face processing workload"
1. Start multiple workers: `python -m scripts.start_worker start`
2. Each worker handles different task queues
3. Monitor with `python -m scripts.start_worker status`

### Scenario 3: Data Scientist
"I want to process images with different combinations of tasks"
1. Create pipeline variations in JSON
2. Enable/disable pipelines as needed
3. Execute with different input parameters

## Troubleshooting Demo Issues

If commands fail:

1. **Check dependencies:**
   ```bash
   python -c "import cv2, numpy, redis, pymongo, loguru; print('All dependencies OK')"
   ```

2. **Verify services:**
   - MongoDB: Should be running on localhost:27017
   - MinIO: Should be running on localhost:9000
   - Redis: Check config.json for connection details

3. **Check image file:**
   ```bash
   dir test.jpg
   ```

4. **Reset if needed:**
   ```bash
   # Clear any stuck processes
   taskkill /F /IM python.exe
   # Restart demo
   python -m tools.pipeline_cli_registry register
   ```

The demo showcases a production-ready pipeline system with JSON configuration, parallel processing, and Celery worker integration!