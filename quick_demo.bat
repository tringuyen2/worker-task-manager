@echo off
echo ========================================
echo WORKER TASK MANAGER v2 - QUICK DEMO
echo ========================================
echo.

echo [1/5] Register pipelines from JSON config...
python -m tools.pipeline_cli_registry register
echo.

echo [2/5] List all registered pipelines...
python -m tools.pipeline_cli_registry list
echo.

echo [3/5] Execute simple face detection pipeline...
python -m tools.pipeline_cli_registry execute simple_face_pipeline "{\"image_path\": \"test.jpg\"}"
echo.

echo [4/5] Execute complex face processing pipeline...
python -m tools.pipeline_cli_registry execute face_processing_pipeline "{\"image_path\": \"test.jpg\"}"
echo.

echo [5/5] Show system capabilities...
python demo_face_processing.py
echo.

echo ========================================
echo QUICK DEMO COMPLETED!
echo ========================================
echo.
echo What you just saw:
echo - 3 pipelines registered (1 built-in + 2 from JSON)
echo - Simple pipeline: Face detection only
echo - Complex pipeline: Face detection + parallel attribute/feature extraction
echo - All configured via JSON without code changes
echo.
pause