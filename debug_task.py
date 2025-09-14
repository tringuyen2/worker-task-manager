#!/usr/bin/env python3
"""
Debug script to understand what's happening in the face_attribute task
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'task_cache', 'face_attribute'))

try:
    from task import Task
    print("Successfully imported face_attribute Task")

    # Create task instance
    task_instance = Task()
    print("Created task instance")

    # Test input that mimics what the pipeline passes
    test_input = {
        "face_bbox": [84, 24, 78, 78],
        "original_image": "test.jpg",
        "face_index": 0
    }

    print(f"Test input: {test_input}")
    print("Attempting to process...")

    result = task_instance.process(test_input)
    print(f"Success! Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()