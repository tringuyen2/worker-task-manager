#!/usr/bin/env python3
"""
JSON Pipeline Configuration Demo
Shows how to define pipelines in JSON and register them
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def show_json_config_structure():
    print("JSON PIPELINE CONFIGURATION SYSTEM")
    print("="*60)
    print()
    print("1. CONFIGURATION FILE: config_pipeline.json")
    print("-"*40)
    print("Define pipelines in a single JSON file with:")
    print("- Pipeline metadata (id, name, description)")
    print("- Step definitions with dependencies")
    print("- Input validation rules")
    print("- Output format specifications")
    print("- Global settings")
    print()

def show_config_example():
    print("2. EXAMPLE PIPELINE CONFIGURATION")
    print("-"*40)
    print("Simple Face Pipeline (JSON-defined):")

    config_example = {
        "pipeline_id": "simple_face_pipeline",
        "name": "Simple Face Detection Pipeline",
        "description": "Basic face detection without attribute analysis",
        "enabled": True,
        "steps": [
            {
                "task_id": "face_detection",
                "timeout": 30,
                "retry_count": 3,
                "depends_on": None,
                "parallel_group": None
            }
        ],
        "input_validation": {
            "required_fields": ["image_path"],
            "supported_formats": ["jpg", "png", "bmp", "tiff"]
        },
        "metadata": {
            "author": "AI Worker System",
            "version": "1.0.0",
            "tags": ["computer_vision", "face_detection"]
        }
    }

    print(json.dumps(config_example, indent=2))
    print()

def show_complex_pipeline():
    print("3. COMPLEX PIPELINE WITH PARALLEL EXECUTION")
    print("-"*40)
    print("Face Processing Pipeline (JSON-defined):")
    print("- Stage 1: face_detection (sequential)")
    print("- Stage 2: face_attribute + face_extractor (parallel)")
    print()

    complex_example = {
        "steps": [
            {
                "task_id": "face_detection",
                "depends_on": None,
                "parallel_group": None
            },
            {
                "task_id": "face_attribute",
                "depends_on": ["face_detection"],
                "parallel_group": "face_analysis"
            },
            {
                "task_id": "face_extractor",
                "depends_on": ["face_detection"],
                "parallel_group": "face_analysis"
            }
        ]
    }

    print(json.dumps(complex_example, indent=2))
    print()

def demo_registration_process():
    print("4. REGISTRATION PROCESS")
    print("-"*40)
    print("Step 1: Load JSON configuration")
    print("Step 2: Validate pipeline definitions")
    print("Step 3: Create pipeline instances")
    print("Step 4: Register with pipeline registry")
    print()

    try:
        from pipeline.json_loader import json_pipeline_loader
        from pipeline.registry import pipeline_registry

        # Load config
        success = json_pipeline_loader.load_config("config_pipeline.json")
        print(f"Config loaded: {success}")

        # Show loaded pipelines
        configs = json_pipeline_loader.get_pipeline_configs()
        print(f"Pipelines defined: {len(configs)}")

        for pipeline_id, config in configs.items():
            enabled = config.get('enabled', True)
            steps = len(config.get('steps', []))
            print(f"  - {pipeline_id}: {enabled} ({steps} steps)")

        # Register pipelines
        count = pipeline_registry.register_json_pipelines()
        print(f"Pipelines registered: {count}")
        print()

    except Exception as e:
        print(f"Demo error: {e}")

def show_cli_commands():
    print("5. CLI COMMANDS")
    print("-"*40)
    print("Show config file contents:")
    print("  python -m tools.pipeline_cli_registry show-config")
    print()
    print("Register pipelines from JSON:")
    print("  python -m tools.pipeline_cli_registry register")
    print()
    print("Register from specific config file:")
    print('  python -m tools.pipeline_cli_registry register --json-config "my_config.json"')
    print()
    print("Execute JSON-defined pipeline:")
    print('  python -m tools.pipeline_cli_registry execute simple_face_pipeline \'{"image_path": "test.jpg"}\'')
    print()
    print("List all registered pipelines:")
    print("  python -m tools.pipeline_cli_registry list")
    print()

def show_benefits():
    print("6. BENEFITS OF JSON CONFIGURATION")
    print("-"*40)
    print("✓ No code changes needed to add new pipelines")
    print("✓ Single file contains all pipeline definitions")
    print("✓ Easy to version control pipeline configurations")
    print("✓ Enable/disable pipelines without code changes")
    print("✓ Supports complex dependency and parallel execution")
    print("✓ Input validation rules defined in config")
    print("✓ Metadata and documentation embedded in config")
    print("✓ Global settings affect all pipelines")
    print()

def demo_execution():
    print("7. EXECUTION DEMO")
    print("-"*40)

    try:
        from pipeline.registry import pipeline_registry

        # Register all pipelines
        total = pipeline_registry.register_all_pipelines()
        print(f"Total pipelines registered: {total}")

        # List available pipelines
        pipelines = pipeline_registry.list_pipelines()
        print(f"Available pipelines: {pipelines}")

        # Show a specific pipeline info
        if "simple_face_pipeline" in pipelines:
            info = pipeline_registry.get_pipeline_info("simple_face_pipeline")
            print(f"\nSimple Face Pipeline Info:")
            print(f"  Name: {info.get('name')}")
            print(f"  Steps: {info.get('steps')}")
            print(f"  Description: {info.get('description')}")

            # Execute pipeline
            print("\nExecuting simple_face_pipeline...")
            result = pipeline_registry.execute_pipeline("simple_face_pipeline", {"image_path": "test.jpg"})
            print(f"Execution status: {result.status.value}")
            print(f"Execution time: {result.execution_time:.2f}s")

            if result.status.value == "completed":
                summary = result.results.get("summary", {})
                print(f"Successful steps: {summary.get('successful_steps', 0)}")
                print("✓ JSON pipeline executed successfully!")

    except Exception as e:
        print(f"Execution demo error: {e}")

def main():
    show_json_config_structure()
    show_config_example()
    show_complex_pipeline()
    demo_registration_process()
    show_cli_commands()
    show_benefits()
    demo_execution()

    print("\n" + "="*60)
    print("JSON PIPELINE SYSTEM READY!")
    print("="*60)
    print("You can now:")
    print("1. Edit config_pipeline.json to add new pipelines")
    print("2. Use CLI commands to register and execute")
    print("3. No code changes needed for new pipelines!")

if __name__ == "__main__":
    main()