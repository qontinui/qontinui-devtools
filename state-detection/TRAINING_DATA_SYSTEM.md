# Training Data System Architecture

Complete system for generating, curating, and exporting training datasets from qontinui automation runs.

## Overview

The training data system automatically captures execution data from qontinui-runner and transforms it into training datasets for qontinui-train. The system consists of three main components:

1. **Data Export** (qontinui-runner) - Automatic capture and export
2. **Data Curation** (qontinui-runner + qontinui-web) - Review and validation
3. **Training Preparation** (qontinui-train) - Format conversion and splitting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        qontinui-runner                           │
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ qontinui library │────────▶│  EventTranslator │             │
│  └──────────────────┘         └──────────────────┘             │
│           │                            │                        │
│           │ match results              │ record events          │
│           │ click events               │                        │
│           ▼                            ▼                        │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ ScreenshotService│◀────────│UnifiedDataCollector            │
│  └──────────────────┘         └──────────────────┘             │
│           │                            │                        │
│           │ screenshots                │ ActionExecutionRecord  │
│           ▼                            ▼                        │
│  ┌─────────────────────────────────────────────────┐           │
│  │       TrainingExportService (callback)          │           │
│  └─────────────────────────────────────────────────┘           │
│                       │                                         │
│                       │ on completion                           │
│                       ▼                                         │
│  ┌─────────────────────────────────────────────────┐           │
│  │           TrainingDataExporter                  │           │
│  │  • Extract bounding boxes from matches          │           │
│  │  • Infer boxes from click locations             │           │
│  │  • Deduplicate images                           │           │
│  │  • Export to intermediate format                │           │
│  │  • Generate COCO format                         │           │
│  └─────────────────────────────────────────────────┘           │
│                       │                                         │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │   Dataset       │
              │   ├── images/   │
              │   ├── annotations/│
              │   ├── manifest.jsonl│
              │   └── metadata.json│
              └─────────────────┘
                        │
        ┌───────────────┴────────────────┐
        │                                │
        ▼                                ▼
┌────────────────────┐      ┌─────────────────────┐
│  qontinui-runner   │      │   qontinui-web      │
│  dataset_viewer.py │      │  Annotation UI      │
│  • Browse          │      │  • Rich editor      │
│  • Validate        │      │  • Batch review     │
│  • Mark good/bad   │      │  • Filter & search  │
│  • Export filtered │      │  • Statistics       │
└────────────────────┘      └─────────────────────┘
        │                                │
        └───────────────┬────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Curated Dataset │
              └─────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  qontinui-train                      │
│                                                      │
│  ┌─────────────────────────────────────────┐       │
│  │    prepare_dataset.py                   │       │
│  │    • Format conversion (COCO/YOLO)      │       │
│  │    • Train/val/test split               │       │
│  │    • Validation & statistics            │       │
│  └─────────────────────────────────────────┘       │
│                       │                             │
│                       ▼                             │
│  ┌─────────────────────────────────────────┐       │
│  │    Training Pipeline                    │       │
│  │    • Load dataset                       │       │
│  │    • Train model                        │       │
│  │    • Evaluate                           │       │
│  └─────────────────────────────────────────┘       │
│                       │                             │
└───────────────────────┼─────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Trained Model  │
              └─────────────────┘
```

## Data Flow

### 1. Capture Phase (qontinui-runner)

**Automatic Capture:**
```python
# Action execution in qontinui library
action.execute()
  ↓
# Event emitted (MATCH_ATTEMPTED, TEXT_TYPED, etc.)
qontinui.reporting.emit_event(...)
  ↓
# EventTranslator records event
event_translator.on_match_attempted(data)
  ↓
# UnifiedDataCollector buffers runtime data
collector.record_match_result(match_summary, screenshot_data)
collector.record_click(x, y, button, target_type)
  ↓
# ActionExecutionRecord created on action completion
record = collector.create_record(...)
  ↓
# Callback to TrainingExportService
training_export_service.add_record(record)
```

**Record Structure:**
```python
ActionExecutionRecord(
    action_id="click-button-123",
    action_type="CLICK",
    screenshot_reference="screenshots/screenshot-0001.png",
    match_summary={
        "image_id": "login_button",
        "confidence": 0.95,
        "location": {"x": 100, "y": 50},
        "template_size": {"width": 200, "height": 100}
    },
    clicked_location=(150, 100),
    click_button="left",
    click_target_type="button",
    active_states_before=["Login"],
    success=True
)
```

### 2. Export Phase (qontinui-runner)

**Transformation Pipeline:**
```python
# 1. Extract bounding boxes from match_summary
bbox_from_match = [
    match["location"]["x"],
    match["location"]["y"],
    match["template_size"]["width"],
    match["template_size"]["height"]
]

# 2. Infer bounding box from click location
bbox_from_click = [
    click_x - 25,  # Center 50x50 box on click
    click_y - 25,
    50,
    50
]

# 3. Deduplicate images by hash
img_hash = hashlib.sha256(image_data).hexdigest()[:16]

# 4. Create annotations
annotation = {
    "bbox": bbox,
    "category_id": category_map[category_name],
    "confidence": match["confidence"] or 1.0,
    "source": "template_matching" or "user_click",
    "verified": source == "user_click"
}

# 5. Write to dataset
exporter.export_records(records, storage_dir)
exporter.export_to_coco(output_path)
```

**Output Format:**
```
dataset/
├── manifest.jsonl              # Appendable line-delimited JSON
├── images/
│   └── <hash>.png              # Deduplicated screenshots
├── annotations/
│   └── <hash>.json             # Bounding boxes + context
├── metadata.json               # Dataset statistics
└── dataset.json                # COCO format export
```

### 3. Curation Phase (qontinui-runner/web)

**CLI Viewer (qontinui-runner):**
```bash
# View summary
python tools/dataset_viewer.py ~/datasets/session_001

# Browse images
python tools/dataset_viewer.py ~/datasets/session_001 --mode browse --limit 20

# Interactive validation
python tools/dataset_viewer.py ~/datasets/session_001 --mode validate

# Export filtered dataset
python tools/dataset_viewer.py ~/datasets/session_001 \
  --mode export \
  --output ~/datasets/curated/v1.0.0 \
  --filter good
```

**Web UI (qontinui-web):**
- Rich annotation editor with canvas-based bounding box editing
- Batch review and filtering
- Statistics dashboard
- Collaborative curation (future)

### 4. Training Preparation (qontinui-train)

**Format Conversion:**
```bash
# Convert to YOLO format with train/val/test split
python -m qontinui_finetune.scripts.prepare_dataset \
  --input ~/datasets/curated/v1.0.0/dataset.json \
  --output ~/datasets/train/v1.0.0 \
  --format yolo \
  --split 0.7,0.2,0.1
```

**Output Structure:**
```
train/v1.0.0/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

## Key Components

### TrainingDataExporter

**Purpose:** Transform ActionExecutionRecords into training datasets

**Key Methods:**
```python
class TrainingDataExporter:
    def export_records(
        self,
        records: List[ActionExecutionRecord],
        storage_dir: Path,
        filter_fn: Optional[callable] = None
    ) -> ExportStatistics

    def export_to_coco(self, output_file: Path) -> None

    def get_summary(self) -> Dict[str, Any]
```

**Features:**
- Extracts bounding boxes from match results
- Infers boxes from click locations
- Deduplicates images by hash
- Tracks categories and generates IDs
- Exports intermediate format (viewable/editable)
- Exports COCO format (training-ready)

### TrainingExportService

**Purpose:** Manage automatic export during runner execution

**Key Methods:**
```python
class TrainingExportService:
    def add_record(self, record: ActionExecutionRecord) -> None

    def export_on_completion(self) -> Optional[ExportStatistics]

    def export_to_coco(self, output_file: Path) -> bool

    def get_summary(self) -> dict
```

**Export Modes:**
- `on_completion`: Export when workflow completes (default)
- `incremental`: Export every N records
- `manual`: Only export when triggered

### UnifiedDataCollector (Enhanced)

**Purpose:** Collect execution data and notify export service

**New Feature:**
```python
class UnifiedDataCollector:
    def __init__(
        self,
        state_memory: Any,
        screenshot_service: Optional[Any] = None,
        record_created_callback: Optional[callable] = None  # NEW
    )

    def create_record(...) -> ActionExecutionRecord:
        record = ActionExecutionRecord(...)

        # Call callback if provided
        if self.record_created_callback:
            self.record_created_callback(record)  # NEW

        return record
```

### Dataset Viewer (CLI)

**Purpose:** Quick validation and filtering from command line

**Modes:**
- `summary`: Show dataset statistics
- `browse`: View images with annotations
- `validate`: Interactive review (mark good/bad)
- `export`: Export filtered subset

## Configuration

### Environment Variables

```bash
# Enable training data export
export QONTINUI_EXPORT_TRAINING_DATA=true

# Set output directory
export QONTINUI_EXPORT_DIR=/path/to/dataset

# Run automation
python qontinui_executor.py config.json
```

### Programmatic Configuration

```python
# In qontinui_executor.py
export_config = ExportConfig(
    enabled=True,
    output_dir=Path("/path/to/dataset"),
    dataset_version="1.0.0",
    export_mode="on_completion",  # or "incremental", "manual"
    batch_size=50,  # For incremental mode
    filter_successful_only=False,
    filter_with_matches=False
)
```

## Annotation Sources

### 1. Template Matching (Automated)

**Source:** Image recognition results from qontinui library

**Characteristics:**
- Confidence score from match algorithm
- Bounding box from template size and location
- Not verified (needs review)
- Good for bulk data generation

**Example:**
```json
{
    "bbox": [100, 50, 200, 100],
    "category_name": "login_button",
    "confidence": 0.95,
    "source": "template_matching",
    "verified": false
}
```

### 2. User Clicks (Human-Validated)

**Source:** Manual interactions during recording

**Characteristics:**
- Confidence 1.0 (human interaction)
- Inferred 50x50px bounding box centered on click
- Pre-verified
- Good for ground truth

**Example:**
```json
{
    "bbox": [125, 75, 50, 50],
    "category_name": "click_target",
    "confidence": 1.0,
    "source": "user_click",
    "verified": true
}
```

## Use Cases

### 1. Fully Automated Data Generation

**Scenario:** Generate large training datasets from automation runs

```bash
# Enable export
export QONTINUI_EXPORT_TRAINING_DATA=true
export QONTINUI_EXPORT_DIR=~/datasets/auto_generated

# Run automation repeatedly
for i in {1..10}; do
    python qontinui_executor.py workflow.json
done

# Result: Large dataset with automated labels
# Next: Validate subset, train model
```

### 2. Manual Recording + Validation

**Scenario:** Create high-quality ground truth dataset

```bash
# Record manual interactions (capture tool enabled)
export QONTINUI_EXPORT_TRAINING_DATA=true
export QONTINUI_EXPORT_DIR=~/datasets/manual_recording
# User performs manual interactions with GUI

# Validate all recordings
python tools/dataset_viewer.py ~/datasets/manual_recording --mode validate

# Export only good examples
python tools/dataset_viewer.py ~/datasets/manual_recording \
  --mode export --filter good --output ~/datasets/ground_truth
```

### 3. Hybrid Approach (Recommended)

**Scenario:** Combine automated + manual data for best results

```bash
# Phase 1: Generate bulk data via automation
export QONTINUI_EXPORT_DIR=~/datasets/hybrid
# Run automation (template matching labels)

# Phase 2: Add manual examples for edge cases
# Enable capture tool, record manual interactions

# Phase 3: Validate samples from both sources
python tools/dataset_viewer.py ~/datasets/hybrid --mode validate

# Phase 4: Export curated dataset
python tools/dataset_viewer.py ~/datasets/hybrid \
  --mode export --filter good --output ~/datasets/curated

# Phase 5: Train model
cd qontinui-train
python scripts/prepare_dataset.py --input ~/datasets/curated/dataset.json
python train.py
```

## Quality Control

### Metrics

- **Coverage:** Percentage of GUI states with training examples
- **Balance:** Distribution across categories
- **Confidence:** Average confidence scores
- **Verification:** Percentage of verified annotations
- **Source Mix:** Ratio of automated vs human-validated

### Best Practices

1. **Mix Sources:** Combine template matching + clicks
2. **Validate Samples:** Review at least 10% of automated labels
3. **Version Datasets:** Track changes and improvements
4. **Incremental Updates:** Add new examples over time
5. **State Coverage:** Ensure all states are represented
6. **Filter Low Confidence:** Remove uncertain automated labels
7. **Document Edge Cases:** Track failure modes and add examples

## Future Enhancements

### Near-Term
- Thumbnail generation for faster browsing
- Advanced filters (confidence ranges, IoU thresholds)
- Annotation quality metrics (precision, recall)
- Export to multiple formats in one pass

### Medium-Term
- Active learning: Select most valuable examples to label
- Semi-automated curation: ML-assisted review
- Annotation guidelines and best practices
- Integration with label versioning systems

### Long-Term
- Multi-user collaboration with conflict resolution
- Real-time dataset updates during live runs
- Transfer learning from existing datasets
- Automated dataset augmentation

## Files Created

### qontinui-runner
```
python-bridge/
├── exporters/
│   ├── __init__.py
│   └── training_data_exporter.py        # Core export logic
├── services/
│   ├── training_export_service.py       # Runner integration
│   └── unified_data_collector.py        # Enhanced with callback
├── tools/
│   └── dataset_viewer.py                # CLI validation tool
├── qontinui_executor.py                 # Integrated export service
└── TRAINING_DATA_EXPORT.md              # User documentation
```

### qontinui-web
```
DATASET_ANNOTATION_API.md                # API specification for web UI
```

### Root
```
TRAINING_DATA_SYSTEM.md                  # This file: Architecture overview
```

## Getting Started

### Quick Start

```bash
# 1. Enable export
export QONTINUI_EXPORT_TRAINING_DATA=true
export QONTINUI_EXPORT_DIR=~/datasets/my_first_dataset

# 2. Run automation
cd qontinui-runner
python python-bridge/qontinui_executor.py your_config.json

# 3. View dataset
python python-bridge/tools/dataset_viewer.py ~/datasets/my_first_dataset

# 4. Validate samples
python python-bridge/tools/dataset_viewer.py ~/datasets/my_first_dataset --mode validate

# 5. Prepare for training
cd ../qontinui-finetune
python scripts/prepare_dataset.py \
  --input ~/datasets/my_first_dataset/dataset.json \
  --output ~/datasets/training/v1 \
  --split 0.7,0.2,0.1
```

### Next Steps

1. Read `qontinui-runner/TRAINING_DATA_EXPORT.md` for detailed usage
2. Explore the CLI viewer: `python tools/dataset_viewer.py --help`
3. Check qontinui-train documentation for training pipeline
4. Review `DATASET_ANNOTATION_API.md` for web UI specification

## Summary

The training data system provides a complete pipeline from automation execution to model training:

✅ **Automatic capture** during runner execution
✅ **Multiple annotation sources** (template matching + clicks)
✅ **Incremental dataset building** with deduplication
✅ **Curation tools** for quality control
✅ **Standard formats** (COCO, YOLO)
✅ **Integration** with qontinui-train

This enables:
- Rapid dataset generation from automation runs
- High-quality ground truth from manual recordings
- Iterative improvement with mixed sources
- Full automation of ML training data pipelines
