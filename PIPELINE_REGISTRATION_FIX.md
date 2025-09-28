# Pipeline Registration - Missing Step Fix

## ⚠️ Important Missing Step

The demo guide was missing the **pipeline registration step**. This has now been fixed in `DEMO_GUIDE_A_TO_Z.md`.

## 🔧 Required Pipeline Registration Step

After registering tasks, you **MUST** register the pipeline:

```bash
# Step D1: Register Built-in Pipeline (REQUIRED)
./venv/bin/python -m tools.pipeline_cli_registry register

# Expected output:
# ✓ Registered pipeline: face_processing_pipeline
# ✓ Registered built-in pipelines
```

## 📋 Complete Corrected Sequence

```bash
# 1. Register Tasks
./venv/bin/python -m tools.task_manager register tasks/examples/face_detection
./venv/bin/python -m tools.task_manager register tasks/examples/face_attribute
./venv/bin/python -m tools.task_manager register tasks/examples/face_extractor

# 2. Register Pipeline (MISSING STEP - NOW ADDED)
./venv/bin/python -m tools.pipeline_cli_registry register

# 3. Verify Pipeline Registration
./venv/bin/python -m tools.pipeline_cli_registry list

# 4. Execute Pipeline
./venv/bin/python -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
```

## ✅ What's Fixed

### Updated in DEMO_GUIDE_A_TO_Z.md:
- ✅ Added **Step D1: Register Built-in Pipeline**
- ✅ Added **Step D4: Register Custom Demo Pipeline (Optional)**
- ✅ Updated **Pipeline Registration Checklist**
- ✅ Added verification commands

### Pipeline Registration Options:
1. **Built-in Pipeline** (Required):
   ```bash
   ./venv/bin/python -m tools.pipeline_cli_registry register
   ```

2. **Custom Demo Pipeline** (Optional - for unique ID testing):
   ```bash
   ./venv/bin/python -m tools.pipeline_cli_registry register --json-config demo_pipeline_config.json
   ```

## 🎯 Why This Step Was Missing

The pipeline registration step was missed because:
- Tasks need to be registered first (which we covered)
- The built-in pipeline auto-registers when imported
- But explicit registration ensures proper setup
- It's required for custom pipelines and configuration

## ✅ Now Complete

The guide is now complete with the pipeline registration step properly documented in the correct sequence!