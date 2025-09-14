@echo off
echo ========================================
echo WORKER TASK MANAGER v2 - DEMO
echo ========================================
echo.

echo Step 1: Show Pipeline Configuration
echo ------------------------------------
python -m tools.pipeline_cli_registry show-config --config-path config_pipeline.json
echo.
pause

echo Step 2: Register All Pipelines
echo --------------------------------
python -m tools.pipeline_cli_registry register
echo.
pause

echo Step 3: List Registered Pipelines
echo ----------------------------------
python -m tools.pipeline_cli_registry list
echo.
pause

echo Step 4: Show Available Tasks
echo -----------------------------
python -m tools.pipeline_cli_registry tasks
echo.
pause

echo Step 5: Execute Simple Face Pipeline (JSON-configured)
echo -------------------------------------------------------
echo Input: {"image_path": "test.jpg"}
python -m tools.pipeline_cli_registry execute simple_face_pipeline "{\"image_path\": \"test.jpg\"}"
echo.
pause

echo Step 6: Execute Complex Face Processing Pipeline
echo -------------------------------------------------
echo Input: {"image_path": "test.jpg"}
python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"test.jpg\"}"
echo.
pause

echo Step 7: Show Pipeline Details
echo ------------------------------
python -m tools.pipeline_cli_registry info face_processing_pipeline
echo.
pause

echo Step 8: Show Worker Commands
echo -----------------------------
echo Manual Celery worker commands:
echo.
echo Face detection worker:
echo celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_detection -n face_detection_worker@%%h
echo.
echo Face attribute worker:
echo celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_attribute -n face_attribute_worker@%%h
echo.
echo Face extractor worker:
echo celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_extractor -n face_extractor_worker@%%h
echo.
pause

echo Step 9: Check Worker Status
echo ----------------------------
python -m scripts.start_worker status
echo.
pause

echo Step 10: Run Complete Demo Script
echo ----------------------------------
python demo_face_processing.py
echo.
pause

echo ========================================
echo DEMO COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Key Features Demonstrated:
echo - JSON Pipeline Configuration
echo - Dynamic Pipeline Registration
echo - Task Execution with Dependencies
echo - Parallel Task Processing
echo - CLI Management Tools
echo - Celery Worker Integration
echo.
echo Next Steps:
echo 1. Edit config_pipeline.json to add new pipelines
echo 2. Start Celery workers: python -m scripts.start_worker start
echo 3. Execute pipelines with: python -m tools.pipeline_cli_registry execute
echo.
pause