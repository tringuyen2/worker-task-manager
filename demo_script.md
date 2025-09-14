# Worker Task Manager v2 - Complete Demo Script

This demo shows the complete pipeline system with JSON configuration, task registration, and Celery workers.

## Prerequisites
- MongoDB running on localhost:27017
- MinIO running on localhost:9000
- Redis running (configured in config.json)
- Python 3.8+ with required packages

## Demo Steps

### Step 1: Show Project Structure
```bash
# Show the main project structure
tree /F /A
# or if tree is not available:
dir /B
```

### Step 2: Show Configuration Files
```bash
# Show main system config
type config.json
echo.
echo ======================================
echo.

# Show pipeline JSON configuration
type config_pipeline.json
```

### Step 3: Show Available Tasks
```bash
# List available tasks from configuration
python -m tools.pipeline_cli_registry tasks
```

### Step 4: Show Pipeline Configuration
```bash
# Display pipeline configuration from JSON
python -m tools.pipeline_cli_registry show-config
```

### Step 5: Register All Pipelines
```bash
# Register both built-in and JSON-configured pipelines
python -m tools.pipeline_cli_registry register
```

### Step 6: List Registered Pipelines
```bash
# Show all registered pipelines
python -m tools.pipeline_cli_registry list
```

### Step 7: Show Pipeline Details
```bash
# Get detailed info about specific pipelines
python -m tools.pipeline_cli_registry info face_processing_pipeline
echo.
python -m tools.pipeline_cli_registry info simple_face_pipeline
```

### Step 8: Execute Simple Face Pipeline (JSON-configured)
```bash
# Execute the JSON-configured simple face detection pipeline
python -m tools.pipeline_cli_registry execute simple_face_pipeline "{\"image_path\": \"test.jpg\"}"
```

### Step 9: Execute Complex Face Processing Pipeline
```bash
# Execute the complex face processing pipeline with parallel tasks
python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"test.jpg\"}"
```

### Step 10: Show Worker Management Commands
```bash
# Show available worker commands
python -m scripts.start_worker --help
```

### Step 11: Check Worker Status (without starting)
```bash
# Check if any workers are currently running
python -m scripts.start_worker status
```

### Step 12: Demo Starting Individual Workers
```bash
echo Starting individual task workers in background...
echo.

# Start face_detection worker (example - don't actually start for demo)
echo "Command to start face_detection worker:"
echo "python -m scripts.start_worker start --task face_detection"
echo.

echo "Command to start face_attribute worker:"
echo "python -m scripts.start_worker start --task face_attribute"
echo.

echo "Command to start face_extractor worker:"
echo "python -m scripts.start_worker start --task face_extractor"
echo.
```

### Step 13: Show Celery Command Examples
```bash
echo Manual Celery worker commands:
echo.
echo "# Face detection worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_detection -n face_detection_worker@%%h"
echo.
echo "# Face attribute worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_attribute -n face_attribute_worker@%%h"
echo.
echo "# Face extractor worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_extractor -n face_extractor_worker@%%h"
echo.
```

### Step 14: Run Complete Demo
```bash
# Run the complete demonstration script
python demo_face_processing.py
```

### Step 15: Run JSON Pipeline Demo
```bash
# Show JSON pipeline system features
python json_pipeline_demo.py
```

### Step 16: Show Pipeline Registration Steps
```bash
# Show step-by-step pipeline registration process
python simple_registration_demo.py
```

### Step 17: Test Different Input Formats
```bash
# Test with file path input
python -m tools.pipeline_cli_registry execute simple_face_pipeline "test.jpg" --format file
```

### Step 18: Show System Capabilities Summary
```bash
echo.
echo ========================================
echo SYSTEM CAPABILITIES SUMMARY
echo ========================================
echo.
echo "✓ JSON Pipeline Configuration"
echo "✓ Dynamic Pipeline Registration"
echo "✓ Task-Specific Celery Workers"
echo "✓ Parallel Task Execution"
echo "✓ Dependency Management"
echo "✓ Input Validation"
echo "✓ Result Aggregation"
echo "✓ CLI Management Tools"
echo "✓ Built-in + JSON Pipeline Support"
echo "✓ MongoDB + MinIO + Redis Integration"
echo.
```

## Quick Demo (Essential Commands Only)

If you want a shorter demo, run these essential commands:

```bash
# 1. Show pipeline config
python -m tools.pipeline_cli_registry show-config

# 2. Register pipelines
python -m tools.pipeline_cli_registry register

# 3. List registered pipelines
python -m tools.pipeline_cli_registry list

# 4. Execute simple pipeline
python -m tools.pipeline_cli_registry execute simple_face_pipeline "{\"image_path\": \"test.jpg\"}"

# 5. Execute complex pipeline
python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"test.jpg\"}"

# 6. Run complete demo
python demo_face_processing.py
```

## Expected Results

1. **Pipeline Registration**: Should show 3 registered pipelines (1 built-in + 2 from JSON)
2. **Simple Pipeline**: Should detect faces and return basic results
3. **Complex Pipeline**: Should detect faces and run parallel attribute/feature extraction
4. **JSON Configuration**: Should load and validate successfully
5. **Worker Commands**: Should show proper Celery worker startup commands

## Troubleshooting

If you encounter issues:

1. Check MongoDB is running: `mongosh --eval "db.adminCommand('ismaster')"`
2. Check MinIO is running: Access http://localhost:9000
3. Check Redis is running: `redis-cli ping`
4. Verify image file exists: `dir test.jpg`
5. Check Python path: `python -c "import sys; print(sys.path)"`