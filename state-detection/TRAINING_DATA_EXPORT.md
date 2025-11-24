# Training Data Export

The qontinui-runner can automatically export training datasets for qontinui-train during automation runs.

## Features

- **Automatic Data Collection**: Captures screenshots, match results, and click locations during execution
- **Multiple Export Formats**: Intermediate format for curation, COCO format for training
- **Incremental Updates**: Supports both batch and streaming export modes
- **Bounding Box Extraction**:
  - Automated labels from template matching results
  - Human-validated labels from user clicks
- **Deduplication**: Automatically deduplicates identical screenshots
- **State Context**: Includes active states and semantic labels

## Quick Start

### Enable Training Data Export

Set environment variables before running the runner:

```bash
export QONTINUI_EXPORT_TRAINING_DATA=true
export QONTINUI_EXPORT_DIR=/path/to/output/dataset

# Run your automation
python qontinui_executor.py your_config.json
```

### Output Structure

The exporter creates the following directory structure:

```
dataset/
├── manifest.jsonl              # One record per line (appendable)
├── images/
│   ├── a1b2c3d4.png           # Deduplicated screenshots
│   ├── e5f6g7h8.png
│   └── ...
├── annotations/
│   ├── a1b2c3d4.json          # Per-image annotations
│   ├── e5f6g7h8.json
│   └── ...
├── metadata.json               # Dataset-level metadata
└── dataset.json                # COCO format export
```

## Data Formats

### Manifest Entry (manifest.jsonl)

```json
{
  "id": "a1b2c3d4",
  "image": "images/a1b2c3d4.png",
  "annotations": "annotations/a1b2c3d4.json",
  "action_id": "click-button-123",
  "action_type": "CLICK",
  "timestamp": 1700000000.0,
  "active_states": ["Login", "MainMenu"],
  "source": "runner_execution",
  "is_new": true,
  "reviewed": false
}
```

### Annotation File (annotations/<hash>.json)

```json
{
  "image_id": "a1b2c3d4",
  "image_filename": "a1b2c3d4.png",
  "image_width": 1920,
  "image_height": 1080,
  "annotations": [
    {
      "bbox": [100, 50, 200, 100],
      "category_id": 0,
      "category_name": "login_button",
      "confidence": 0.95,
      "source": "template_matching",
      "verified": false
    },
    {
      "bbox": [350, 250, 50, 50],
      "category_id": 1,
      "category_name": "click_target",
      "confidence": 1.0,
      "source": "user_click",
      "verified": true
    }
  ],
  "context": {
    "action_type": "CLICK",
    "active_states": ["Login"],
    "timestamp": 1700000000.0,
    "success": true
  },
  "version": "1.0.0"
}
```

### Metadata (metadata.json)

```json
{
  "dataset_version": "1.0.0",
  "created": "2025-11-24T12:00:00",
  "total_images": 150,
  "total_annotations": 287,
  "category_map": {
    "login_button": 0,
    "submit_button": 1,
    "menu_icon": 2
  },
  "categories": [
    {"id": 0, "name": "login_button"},
    {"id": 1, "name": "submit_button"},
    {"id": 2, "name": "menu_icon"}
  ],
  "statistics": {
    "total_records_processed": 200,
    "records_with_screenshots": 150,
    "records_with_matches": 120,
    "records_with_clicks": 80,
    "skipped_records": 50,
    "export_time_seconds": 5.3
  },
  "format": "intermediate",
  "description": "Training dataset exported from qontinui-runner execution data"
}
```

## Advanced Configuration

### Export Modes

Modify `qontinui_executor.py` to configure export behavior:

```python
export_config = ExportConfig(
    enabled=True,
    output_dir=Path(export_dir),
    dataset_version="1.0.0",

    # Export modes:
    # - "on_completion": Export when run completes (default)
    # - "incremental": Export every N records
    # - "manual": Only export when manually triggered
    export_mode="incremental",

    # For incremental mode
    batch_size=50,  # Export every 50 records

    # Filters
    filter_successful_only=False,  # Include failed actions
    filter_with_matches=False      # Include actions without matches
)
```

### Filtering Records

Apply custom filters during export:

```python
# Only export records with high-confidence matches
exporter.export_records(
    records=records,
    storage_dir=storage_dir,
    filter_fn=lambda r: r.match_summary and r.match_summary.get("confidence", 0) > 0.8
)
```

## Integration with qontinui-train

### Step 1: Export from Runner

```bash
export QONTINUI_EXPORT_TRAINING_DATA=true
export QONTINUI_EXPORT_DIR=~/datasets/session_001
python qontinui_executor.py config.json
```

### Step 2: (Optional) View and Curate Dataset

Use qontinui-web or the runner's validation UI to review annotations:

- Mark good/bad examples
- Correct bounding boxes
- Filter by confidence or state

### Step 3: Prepare for Training (qontinui-train)

```bash
cd qontinui-finetune

# Convert to training format with train/val/test split
python scripts/prepare_dataset.py \
  --input ~/datasets/session_001/dataset.json \
  --output ~/datasets/train/v1.0.0 \
  --format coco \
  --split 0.7,0.2,0.1
```

### Step 4: Train Model

```bash
# Use your training pipeline with the prepared dataset
python train.py --dataset ~/datasets/train/v1.0.0
```

## Annotation Sources

The exporter creates annotations from two sources:

### 1. Template Matching (Automated)

- **Source**: `match_summary` from image recognition
- **Confidence**: Match confidence score (0.0-1.0)
- **Verified**: `false` (needs human review)
- **Bounding Box**: Extracted from template size and match location

```python
{
    "bbox": [x, y, width, height],
    "category_name": "login_button",
    "confidence": 0.95,
    "source": "template_matching",
    "verified": false
}
```

### 2. User Clicks (Human-Validated)

- **Source**: `clicked_location` from manual interactions
- **Confidence**: `1.0` (human interaction)
- **Verified**: `true` (pre-validated)
- **Bounding Box**: Inferred 50x50px box centered on click

```python
{
    "bbox": [x-25, y-25, 50, 50],
    "category_name": "click_target",
    "confidence": 1.0,
    "source": "user_click",
    "verified": true
}
```

## Best Practices

### 1. Incremental Dataset Building

Build datasets over multiple sessions:

```bash
# Session 1
export QONTINUI_EXPORT_DIR=~/datasets/my_app
python qontinui_executor.py session1.json

# Session 2 (appends to existing dataset)
export QONTINUI_EXPORT_DIR=~/datasets/my_app
python qontinui_executor.py session2.json

# Session 3
export QONTINUI_EXPORT_DIR=~/datasets/my_app
python qontinui_executor.py session3.json
```

### 2. Mix Automated and Manual Data

- **Automated runs**: Generate bulk data with template matching
- **Manual recordings**: Capture high-quality human interactions
- **Combined**: Best of both worlds - quantity + quality

### 3. State-Based Organization

Export creates state context for semantic grouping:

```python
# Filter annotations by state
annotations = [a for a in annotations if "Login" in a["context"]["active_states"]]
```

### 4. Version Your Datasets

Use semantic versioning for datasets:

- `1.0.0`: Initial dataset
- `1.1.0`: Added 500 new examples
- `2.0.0`: Changed annotation format or categories

## Troubleshooting

### No Data Exported

Check:
1. Environment variables are set correctly
2. Export directory is writable
3. Screenshots are being captured (check run_dir/screenshots/)
4. Actions have `screenshot_reference` populated

### Missing Bounding Boxes

- Template matching requires `match_summary` with `location` and `template_size`
- Clicks require `clicked_location` to be recorded
- Check that EventTranslator is connected to UnifiedDataCollector

### Duplicate Images

This is normal - the exporter deduplicates by image hash. Duplicate screenshots are stored once but referenced multiple times in the manifest.

### Large Dataset Size

Reduce dataset size by:
- Enabling filters (`filter_successful_only`, `filter_with_matches`)
- Adjusting image quality/resolution at screenshot capture level
- Periodically archiving old datasets

## API Reference

### TrainingDataExporter

```python
from exporters.training_data_exporter import TrainingDataExporter

exporter = TrainingDataExporter(
    output_dir=Path("dataset"),
    dataset_version="1.0.0"
)

# Export records
stats = exporter.export_records(
    records=records,
    storage_dir=run_dir,
    filter_fn=lambda r: r.success
)

# Convert to COCO
exporter.export_to_coco(Path("dataset/dataset.json"))

# Get summary
summary = exporter.get_summary()
```

### TrainingExportService

```python
from services.training_export_service import TrainingExportService, ExportConfig

config = ExportConfig(
    enabled=True,
    output_dir=Path("dataset"),
    export_mode="incremental",
    batch_size=50
)

service = TrainingExportService(config, storage_dir=run_dir)

# Records are automatically added via callback
# ...

# Manual export
stats = service.export_now()

# Export to COCO
service.export_to_coco(Path("dataset/dataset.json"))

# Get summary
summary = service.get_summary()
```

## Future Enhancements

- Active learning: Select most valuable examples to label
- Multi-format support: YOLO, Pascal VOC, TensorFlow TFRecord
- Dataset versioning and diffs
- Annotation quality metrics
- Integration with label annotation tools (labelImg, CVAT)
