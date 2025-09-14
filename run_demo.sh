#!/bin/bash

echo "========================================"
echo "WORKER TASK MANAGER v2 - DEMO"
echo "========================================"
echo

echo "Step 1: Show Pipeline Configuration"
echo "------------------------------------"
python3 -m tools.pipeline_cli_registry show-config --config-path config_pipeline.json
echo
read -p "Press Enter to continue..."

echo "Step 2: Register All Pipelines"
echo "--------------------------------"
python3 -m tools.pipeline_cli_registry register
echo
read -p "Press Enter to continue..."

echo "Step 3: List Registered Pipelines"
echo "----------------------------------"
python3 -m tools.pipeline_cli_registry list
echo
read -p "Press Enter to continue..."

echo "Step 4: Show Available Tasks"
echo "-----------------------------"
python3 -m tools.pipeline_cli_registry tasks
echo
read -p "Press Enter to continue..."

echo "Step 5: Execute Simple Face Pipeline (JSON-configured)"
echo "-------------------------------------------------------"
echo "Input: {\"image_path\": \"test.jpg\"}"
python3 -m tools.pipeline_cli_registry execute simple_face_pipeline '{"image_path": "test.jpg"}'
echo
read -p "Press Enter to continue..."

echo "Step 6: Execute Complex Face Processing Pipeline"
echo "-------------------------------------------------"
echo "Input: {\"image_path\": \"test.jpg\"}"
python3 -m tools.pipeline_cli_registry execute face_processing_pipeline '{"image_path": "test.jpg"}'
echo
read -p "Press Enter to continue..."

echo "Step 7: Show Pipeline Details"
echo "------------------------------"
python3 -m tools.pipeline_cli_registry info face_processing_pipeline
echo
read -p "Press Enter to continue..."

echo "Step 8: Show Worker Commands"
echo "-----------------------------"
echo "Manual Celery worker commands:"
echo
echo "Face detection worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_detection -n face_detection_worker@%h"
echo
echo "Face attribute worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_attribute -n face_attribute_worker@%h"
echo
echo "Face extractor worker:"
echo "celery -A worker.celery_app:celery_app worker --loglevel=INFO -Q face_extractor -n face_extractor_worker@%h"
echo
read -p "Press Enter to continue..."

echo "Step 9: Check Worker Status"
echo "----------------------------"
python3 -m scripts.start_worker status
echo
read -p "Press Enter to continue..."

echo "Step 10: Run Complete Demo Script"
echo "----------------------------------"
python3 demo_face_processing.py
echo
read -p "Press Enter to continue..."

echo "========================================"
echo "DEMO COMPLETED SUCCESSFULLY!"
echo "========================================"
echo
echo "Key Features Demonstrated:"
echo "- JSON Pipeline Configuration"
echo "- Dynamic Pipeline Registration"
echo "- Task Execution with Dependencies"
echo "- Parallel Task Processing"
echo "- CLI Management Tools"
echo "- Celery Worker Integration"
echo
echo "Next Steps:"
echo "1. Edit config_pipeline.json to add new pipelines"
echo "2. Start Celery workers: python3 -m scripts.start_worker start"
echo "3. Execute pipelines with: python3 -m tools.pipeline_cli_registry execute"
echo