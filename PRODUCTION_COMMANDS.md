# Production Commands for ID-Based Pipeline Demo

## Prerequisites ✅

```bash
# Services running
docker compose up -d
docker compose ps  # Check status

# Dependencies installed
./venv/bin/pip install opencv-python numpy celery redis pymongo minio

# Test image available
ls -la test.jpg
```

## Step 1: Register Tasks with Unique IDs

```bash
# Register face detection task
./venv/bin/python -m tools.task_manager register demo_face_detection_task.json

# Register face attribute task
./venv/bin/python -m tools.task_manager register demo_face_attribute_task.json

# Register face extractor task
./venv/bin/python -m tools.task_manager register demo_face_extractor_task.json
```

**Expected Output:**
```
✓ Task validation passed
✓ Task uploaded to MinIO
✓ Task registered in MongoDB
Task ID: demo_face_detection (input_001 → output_001)
```

## Step 2: Verify Tasks Exist

```bash
# List all registered tasks
./venv/bin/python -m tools.task_manager list
```

**Expected Output:**
```
✅ demo_face_detection (face_detection_input_001 → face_detection_output_001)
✅ demo_face_attribute (face_attribute_input_002 ← output_001_faces_array)
✅ demo_face_extractor (face_extractor_input_003 ← output_001_faces_array)
```

```bash
# Get detailed task info
./venv/bin/python -m tools.task_manager info demo_face_detection
```

**Expected Output:**
```
Task ID: demo_face_detection
Input ID: face_detection_input_001
Output ID: face_detection_output_001
Primary Output: output_001_faces_array
Input Fields: input_001_image_path, input_001_confidence
```

## Step 3: Register Pipeline with ID Mapping

```bash
# Register pipeline from JSON config
./venv/bin/python -m tools.pipeline_cli_registry register --json-config demo_pipeline_config.json
```

**Expected Output:**
```
✅ Pipeline registered: demo_face_processing_pipeline
✅ Data flow mapping configured:
   - Step 1: output_001_faces_array
   - Step 2: input_002_faces_array (maps from output_001)
   - Step 3: input_003_faces_array (maps from output_001)
✅ Parallel group: parallel_analysis (steps 2 & 3)
```

## Step 4: Verify Pipeline Registration

```bash
# List registered pipelines
./venv/bin/python -m tools.pipeline_cli_registry list
```

**Expected Output:**
```
✅ demo_face_processing_pipeline (enabled)
   - Steps: 3 (1 sequential, 2 parallel)
   - Data flow: ID-based mapping configured
   - Parallel group: parallel_analysis
```

```bash
# Get pipeline details
./venv/bin/python -m tools.pipeline_cli_registry info demo_face_processing_pipeline
```

**Expected Output:**
```
Pipeline ID: demo_face_processing_pipeline
Steps:
  1. demo_face_detection (no dependencies)
  2. demo_face_attribute (depends_on: step_1, parallel_group: parallel_analysis)
  3. demo_face_extractor (depends_on: step_1, parallel_group: parallel_analysis)

Data Flow Mapping:
  output_001_faces_array → input_002_faces_array
  output_001_faces_array → input_003_faces_array
```

## Step 5: Execute Pipeline

### Direct Execution (Without Workers)
```bash
# Execute pipeline directly
./venv/bin/python -m tools.pipeline_cli_registry execute demo_face_processing_pipeline '{"image_path": "test.jpg"}'
```

### Production Execution (With Celery Workers)
```bash
# Start workers first
./venv/bin/python -m scripts.start_worker start --task demo_face_detection
./venv/bin/python -m scripts.start_worker start --task demo_face_attribute
./venv/bin/python -m scripts.start_worker start --task demo_face_extractor

# Execute with workers
./venv/bin/python -m tools.pipeline_cli_registry execute demo_face_processing_pipeline '{"image_path": "test.jpg"}' --workers
```

## Step 6: Expected Results

### Execution Flow Trace
```json
{
  "pipeline_id": "demo_face_processing_pipeline",
  "execution_trace": {
    "step_1": {
      "task_id": "demo_face_detection",
      "input_id": "face_detection_input_001",
      "input_mapping": {
        "image_path": "input_001_image_path"
      },
      "output_id": "face_detection_output_001",
      "primary_output": "output_001_faces_array",
      "execution_time": "0.3s"
    },
    "step_2": {
      "task_id": "demo_face_attribute",
      "input_id": "face_attribute_input_002",
      "input_mapping": {
        "faces": "output_001_faces_array → input_002_faces_array",
        "image_path": "input_001_image_path → input_002_image_path"
      },
      "output_id": "face_attribute_output_002",
      "parallel_group": "parallel_analysis",
      "execution_time": "0.4s"
    },
    "step_3": {
      "task_id": "demo_face_extractor",
      "input_id": "face_extractor_input_003",
      "input_mapping": {
        "faces": "output_001_faces_array → input_003_faces_array",
        "image_path": "input_001_image_path → input_003_image_path"
      },
      "output_id": "face_extractor_output_003",
      "parallel_group": "parallel_analysis",
      "execution_time": "0.5s"
    }
  }
}
```

### Final Output
```json
{
  "pipeline_id": "demo_face_processing_pipeline",
  "status": "completed",
  "total_execution_time": "0.8s",
  "parallel_speedup": "2x",
  "faces": [
    {
      "face_id": 0,
      "detection_data": {
        "bbox": [120, 80, 180, 220],
        "confidence": 0.95,
        "source": "output_001_faces_array"
      },
      "attributes_data": {
        "age": 28,
        "gender": "male",
        "emotion": "happy",
        "confidence": 0.89,
        "source": "output_002_faces_with_attributes"
      },
      "features_data": {
        "feature_vector": [0.1, 0.2, "...", 0.512],
        "feature_dimension": 512,
        "is_normalized": true,
        "source": "output_003_faces_with_features"
      }
    }
  ],
  "data_lineage": {
    "face_detection": "output_001_faces_array",
    "face_attribute_input": "input_002_faces_array (from output_001)",
    "face_extractor_input": "input_003_faces_array (from output_001)"
  }
}
```

## Data Flow Verification

### ID Mapping Verification
```bash
# Verify field mappings
./venv/bin/python -c "
import json
with open('demo_pipeline_config.json') as f:
    config = json.load(f)

flow = config['data_flow_mapping']['primary_data_flow']
print('✅ Data Flow Mappings:')
for mapping in flow:
    print(f'   {mapping}')
"
```

**Expected Output:**
```
✅ Data Flow Mappings:
   output_001_faces_array → input_002_faces_array
   output_001_faces_array → input_003_faces_array
```

## Monitoring and Debugging

### Check Task Execution
```bash
# Monitor worker status
./venv/bin/python -m scripts.start_worker status

# View execution history
./venv/bin/python -m tools.worker_cli executions --limit 10

# Check specific task logs
./venv/bin/python -m tools.worker_cli logs demo_face_detection
```

### Monitor Pipeline Execution
```bash
# Real-time pipeline monitoring
./venv/bin/python -m tools.pipeline_cli_registry monitor demo_face_processing_pipeline

# Check data flow validation
./venv/bin/python -m tools.pipeline_cli_registry validate demo_face_processing_pipeline
```

## Summary

This production workflow demonstrates:

1. ✅ **Unique ID System**: Each task has unique input/output IDs
2. ✅ **Explicit Data Mapping**: `output_001_faces_array` → `input_002_faces_array` & `input_003_faces_array`
3. ✅ **Parallel Execution**: Steps 2 & 3 run simultaneously with shared input
4. ✅ **Data Lineage**: Complete traceability from input to final output
5. ✅ **Production Ready**: Works with Celery workers and distributed processing

**Key Achievement**: `output 1 of task face_detection` is explicitly mapped as `input 2 of task face_attribute` and `input 3 of task face_extractor` using unique, traceable field IDs!