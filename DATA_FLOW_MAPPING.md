# Data Flow Mapping with Unique IDs

## 🎯 Overview

This document demonstrates how to manage inputs and outputs with unique IDs so you can explicitly map outputs from one task as inputs to another task.

## 🔄 ID-Based Data Flow System

### Input/Output ID Structure

Each task has unique input and output IDs:
- **Input ID Pattern**: `{task_name}_input_{sequence_number}`
- **Output ID Pattern**: `{task_name}_output_{sequence_number}`
- **Field ID Pattern**: `{input/output}_{sequence_number}_{field_name}`

## 📋 Task Configuration Summary

### Task 1: demo_face_detection
```json
Input ID:  "face_detection_input_001"
Output ID: "face_detection_output_001"

Key Fields:
- input_001_image_path     → Pipeline input
- input_001_confidence     → Optional threshold
- output_001_faces_array   → Primary output (faces detected)
- output_001_face_count    → Metadata
- output_001_image_size    → Image dimensions
```

### Task 2: demo_face_attribute
```json
Input ID:  "face_attribute_input_002"
Output ID: "face_attribute_output_002"

Key Fields:
- input_002_faces_array           ← output_001_faces_array
- input_002_image_path            ← input_001_image_path
- output_002_faces_with_attributes → Primary output (faces + attributes)
- output_002_age                  → Age predictions
- output_002_gender               → Gender predictions
- output_002_emotion              → Emotion predictions
```

### Task 3: demo_face_extractor
```json
Input ID:  "face_extractor_input_003"
Output ID: "face_extractor_output_003"

Key Fields:
- input_003_faces_array           ← output_001_faces_array
- input_003_image_path            ← input_001_image_path
- output_003_faces_with_features  → Primary output (faces + features)
- output_003_feature_vector       → Feature vectors
- output_003_feature_dimension    → Vector dimensions
```

## 🔗 Data Flow Mapping

### Primary Data Flow Chain

```
Pipeline Input
    ↓
┌─────────────────────────────────────┐
│ demo_face_detection                  │
│ Input:  face_detection_input_001    │
│ Output: face_detection_output_001   │
│ Key: output_001_faces_array         │
└─────────────────────────────────────┘
    ↓ output_001_faces_array
    ├─────────────────────┬─────────────────────┐
    ↓                     ↓                     ↓
┌─────────────────┐   ┌─────────────────┐
│ demo_face_attr  │   │ demo_face_extr  │
│ Input: 002      │   │ Input: 003      │
│ Output: 002     │   │ Output: 003     │
└─────────────────┘   └─────────────────┘
```

### Explicit Field Mappings

#### Step 1 → Step 2 (face_detection → face_attribute)
```json
{
  "source_task": "demo_face_detection",
  "source_output_id": "face_detection_output_001",
  "target_task": "demo_face_attribute",
  "target_input_id": "face_attribute_input_002",
  "field_mappings": {
    "output_001_faces_array": "input_002_faces_array",
    "input_001_image_path": "input_002_image_path"
  }
}
```

#### Step 1 → Step 3 (face_detection → face_extractor)
```json
{
  "source_task": "demo_face_detection",
  "source_output_id": "face_detection_output_001",
  "target_task": "demo_face_extractor",
  "target_input_id": "face_extractor_input_003",
  "field_mappings": {
    "output_001_faces_array": "input_003_faces_array",
    "input_001_image_path": "input_003_image_path"
  }
}
```

## 📊 Pipeline Configuration Example

```json
{
  "steps": [
    {
      "step_id": "step_1_face_detection",
      "task_id": "demo_face_detection",
      "input_mapping": {
        "source": "pipeline_input",
        "mapping": {
          "image_path": "input_001_image_path",
          "confidence_threshold": "input_001_confidence"
        }
      },
      "output_mapping": {
        "output_id": "face_detection_output_001",
        "primary_outputs": ["output_001_faces_array"]
      }
    },
    {
      "step_id": "step_2_face_attributes",
      "task_id": "demo_face_attribute",
      "depends_on": ["step_1_face_detection"],
      "parallel_group": "parallel_analysis",
      "input_mapping": {
        "source": "step_1_face_detection",
        "source_output_id": "face_detection_output_001",
        "mapping": {
          "faces": "output_001_faces_array",
          "image_path": "input_001_image_path"
        },
        "target_input_id": "face_attribute_input_002"
      }
    },
    {
      "step_id": "step_3_face_features",
      "task_id": "demo_face_extractor",
      "depends_on": ["step_1_face_detection"],
      "parallel_group": "parallel_analysis",
      "input_mapping": {
        "source": "step_1_face_detection",
        "source_output_id": "face_detection_output_001",
        "mapping": {
          "faces": "output_001_faces_array",
          "image_path": "input_001_image_path"
        },
        "target_input_id": "face_extractor_input_003"
      }
    }
  ]
}
```

## 🚀 Execution Example

### Step-by-Step Execution with ID Tracking

#### Input
```json
{
  "image_path": "test.jpg",
  "confidence_threshold": 0.3
}
```

#### Step 1: Face Detection
**Input Mapping:**
- `image_path` → `input_001_image_path`
- `confidence_threshold` → `input_001_confidence`

**Execution:**
```json
{
  "task_id": "demo_face_detection",
  "input_id": "face_detection_input_001",
  "input": {
    "input_001_image_path": "test.jpg",
    "input_001_confidence": 0.3
  }
}
```

**Output:**
```json
{
  "output_id": "face_detection_output_001",
  "output_001_faces_array": [
    {
      "output_001_face_id": 0,
      "output_001_bbox": [120, 80, 180, 220],
      "output_001_confidence": 0.95
    }
  ],
  "output_001_face_count": 1,
  "output_001_image_size": [640, 480]
}
```

#### Step 2: Face Attribute Analysis (Parallel)
**Input Mapping:**
- `output_001_faces_array` → `input_002_faces_array`
- `input_001_image_path` → `input_002_image_path`

**Execution:**
```json
{
  "task_id": "demo_face_attribute",
  "input_id": "face_attribute_input_002",
  "input": {
    "input_002_faces_array": [
      {
        "input_002_face_id": 0,
        "input_002_bbox": [120, 80, 180, 220],
        "input_002_confidence": 0.95
      }
    ],
    "input_002_image_path": "test.jpg"
  }
}
```

**Output:**
```json
{
  "output_id": "face_attribute_output_002",
  "output_002_faces_with_attributes": [
    {
      "output_002_face_id": 0,
      "output_002_bbox": [120, 80, 180, 220],
      "output_002_attributes": {
        "output_002_age": 28,
        "output_002_gender": "male",
        "output_002_emotion": "happy",
        "output_002_attr_confidence": 0.89
      }
    }
  ]
}
```

#### Step 3: Face Feature Extraction (Parallel)
**Input Mapping:**
- `output_001_faces_array` → `input_003_faces_array`
- `input_001_image_path` → `input_003_image_path`

**Execution:**
```json
{
  "task_id": "demo_face_extractor",
  "input_id": "face_extractor_input_003",
  "input": {
    "input_003_faces_array": [
      {
        "input_003_face_id": 0,
        "input_003_bbox": [120, 80, 180, 220],
        "input_003_confidence": 0.95
      }
    ],
    "input_003_image_path": "test.jpg"
  }
}
```

**Output:**
```json
{
  "output_id": "face_extractor_output_003",
  "output_003_faces_with_features": [
    {
      "output_003_face_id": 0,
      "output_003_bbox": [120, 80, 180, 220],
      "output_003_features": {
        "output_003_feature_vector": [0.1, 0.2, 0.3, "...", 0.512],
        "output_003_feature_dimension": 512,
        "output_003_is_normalized": true,
        "output_003_extraction_confidence": 0.92
      }
    }
  ]
}
```

## 🔧 Key Benefits

1. **Explicit Data Mapping**: Clear traceability of data flow between tasks
2. **Unique Identification**: Every input/output field has a unique ID
3. **Parallel Execution**: Multiple tasks can consume the same output simultaneously
4. **Data Validation**: Field-level validation and type checking
5. **Debugging**: Easy to trace data flow issues with unique IDs
6. **Version Control**: Track changes to input/output schemas

## 📝 Implementation Notes

### Task Configuration Requirements
- Each task must define `input_id` and `output_id`
- All fields must have unique `field_id` attributes
- Source field mapping must be explicit in `input_schema.input_mapping`

### Pipeline Configuration Requirements
- Each step must define `input_mapping` and `output_mapping`
- Dependencies must be explicitly declared with source output IDs
- Parallel groups share the same source outputs

### Runtime Requirements
- The pipeline executor must map fields by ID, not by name
- Data validation must check field IDs match expected types
- Parallel tasks must receive copies of the source data

## 🎯 Summary

This ID-based system ensures:
- **output_001_faces_array** from `demo_face_detection` becomes **input_002_faces_array** for `demo_face_attribute`
- **output_001_faces_array** from `demo_face_detection` becomes **input_003_faces_array** for `demo_face_extractor`
- Both parallel tasks share the same source data but have unique input/output identifiers
- Complete data lineage tracking through the entire pipeline