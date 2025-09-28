#!/usr/bin/env python3
"""
Get Task and Pipeline Information
Shows how to retrieve registered task and pipeline information from the system.
"""

import json
import os
import sys
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def get_cached_tasks():
    """Get information about cached tasks."""
    print_section("CACHED TASKS INFO")

    cache_index_path = "task_cache/cache_index.json"
    if os.path.exists(cache_index_path):
        with open(cache_index_path, 'r') as f:
            cache_index = json.load(f)

        print(f"Found {len(cache_index)} cached tasks:")
        for task_id, info in cache_index.items():
            print(f"✅ {task_id}")
            print(f"   Cached at: {info['cached_at']}")

            # Read task configuration
            task_config_path = f"task_cache/{task_id}/task.json"
            if os.path.exists(task_config_path):
                with open(task_config_path, 'r') as f:
                    task_config = json.load(f)

                print(f"   Name: {task_config.get('name', 'N/A')}")
                print(f"   Version: {task_config.get('version', 'N/A')}")
                print(f"   Queue: {task_config.get('queue', 'N/A')}")
                print(f"   Priority: {task_config.get('priority', 'N/A')}")

                # Show input/output info
                input_schema = task_config.get('input_schema', {})
                output_schema = task_config.get('output_schema', {})

                if 'properties' in input_schema:
                    inputs = list(input_schema['properties'].keys())
                    print(f"   Inputs: {', '.join(inputs[:3])}{'...' if len(inputs) > 3 else ''}")

                if 'properties' in output_schema:
                    outputs = list(output_schema['properties'].keys())
                    print(f"   Outputs: {', '.join(outputs[:3])}{'...' if len(outputs) > 3 else ''}")
            print()
    else:
        print("❌ No task cache index found")

def get_demo_tasks():
    """Get information about demo tasks with unique IDs."""
    print_section("DEMO TASKS WITH UNIQUE IDs")

    demo_tasks = [
        "demo_face_detection_task.json",
        "demo_face_attribute_task.json",
        "demo_face_extractor_task.json"
    ]

    for task_file in demo_tasks:
        if os.path.exists(task_file):
            with open(task_file, 'r') as f:
                task_config = json.load(f)

            print(f"✅ {task_config.get('task_id', 'N/A')}")
            print(f"   File: {task_file}")
            print(f"   Name: {task_config.get('name', 'N/A')}")

            # Show unique ID information
            input_schema = task_config.get('input_schema', {})
            output_schema = task_config.get('output_schema', {})

            if 'input_id' in input_schema:
                print(f"   Input ID: {input_schema['input_id']}")

            if 'output_id' in output_schema:
                print(f"   Output ID: {output_schema['output_id']}")

            # Show input mapping if available
            if 'input_mapping' in input_schema:
                mapping = input_schema['input_mapping']
                print(f"   Source Task: {mapping.get('source_task', 'N/A')}")
                print(f"   Source Output: {mapping.get('source_output_id', 'N/A')}")

            # Show output mapping if available
            if 'output_mapping' in output_schema:
                mapping = output_schema['output_mapping']
                print(f"   Primary Output: {mapping.get('primary_output', 'N/A')}")

            print()
        else:
            print(f"❌ {task_file} not found")

def get_pipeline_configurations():
    """Get information about pipeline configurations."""
    print_section("PIPELINE CONFIGURATIONS")

    # Check standard pipeline config
    config_files = [
        "config_pipeline.json",
        "demo_pipeline_config.json"
    ]

    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"\n📄 {config_file}")
            with open(config_file, 'r') as f:
                config = json.load(f)

            pipelines = config.get('pipelines', {})
            print(f"Found {len(pipelines)} pipeline(s):")

            for pipeline_id, pipeline_config in pipelines.items():
                print(f"\n✅ {pipeline_id}")
                print(f"   Name: {pipeline_config.get('name', 'N/A')}")
                print(f"   Enabled: {pipeline_config.get('enabled', False)}")
                print(f"   Steps: {len(pipeline_config.get('steps', []))}")

                # Show steps information
                steps = pipeline_config.get('steps', [])
                for i, step in enumerate(steps, 1):
                    task_id = step.get('task_id', 'N/A')
                    depends_on = step.get('depends_on', None)
                    parallel_group = step.get('parallel_group', None)

                    print(f"     Step {i}: {task_id}")
                    if depends_on:
                        print(f"       Depends on: {depends_on}")
                    if parallel_group:
                        print(f"       Parallel group: {parallel_group}")

                    # Show input/output mapping if available
                    if 'input_mapping' in step:
                        mapping = step['input_mapping']
                        source = mapping.get('source', 'N/A')
                        print(f"       Input source: {source}")

                    if 'output_mapping' in step:
                        mapping = step['output_mapping']
                        output_id = mapping.get('output_id', 'N/A')
                        print(f"       Output ID: {output_id}")

                # Show data flow mapping if available
                if 'data_flow_mapping' in config:
                    flow_mapping = config['data_flow_mapping']
                    print(f"\n   📊 Data Flow Mapping:")

                    if 'primary_data_flow' in flow_mapping.get('id_mapping_rules', {}):
                        flows = flow_mapping['id_mapping_rules']['primary_data_flow']
                        for flow in flows:
                            print(f"     {flow}")

        else:
            print(f"❌ {config_file} not found")

def show_commands():
    """Show the commands to get registered information."""
    print_section("COMMANDS TO GET REGISTERED INFO")

    print("📋 To get registered tasks:")
    print("./venv/bin/python -m tools.task_manager list")
    print("./venv/bin/python -m tools.task_manager info <task_id>")
    print()

    print("📋 To get registered pipelines:")
    print("./venv/bin/python -m tools.pipeline_cli_registry list")
    print("./venv/bin/python -m tools.pipeline_cli_registry info <pipeline_id>")
    print("./venv/bin/python -m tools.pipeline_cli_registry show-config")
    print()

    print("📋 To register demo tasks:")
    print("./venv/bin/python -m tools.task_manager register demo_face_detection_task.json")
    print("./venv/bin/python -m tools.task_manager register demo_face_attribute_task.json")
    print("./venv/bin/python -m tools.task_manager register demo_face_extractor_task.json")
    print()

    print("📋 To register demo pipeline:")
    print("./venv/bin/python -m tools.pipeline_cli_registry register --json-config demo_pipeline_config.json")

def main():
    """Main function to display all information."""
    print("🔍 TASK AND PIPELINE INFORMATION RETRIEVAL")

    # Get cached tasks
    get_cached_tasks()

    # Get demo tasks with unique IDs
    get_demo_tasks()

    # Get pipeline configurations
    get_pipeline_configurations()

    # Show commands
    show_commands()

    print(f"\n{'='*60}")
    print("✅ Information retrieval complete!")
    print("Use the commands above to get real-time registered information.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()