# Dataset Annotation API

API specification for the web-based dataset annotation interface in qontinui-web.

## Overview

The dataset annotation interface provides a rich web UI for:
- Browsing training datasets exported from qontinui-runner
- Reviewing and validating annotations
- Editing bounding boxes
- Filtering and searching
- Exporting curated datasets

## API Endpoints

### Dataset Management

#### List Datasets

```
GET /api/datasets
```

**Response:**
```json
{
  "datasets": [
    {
      "id": "session_001",
      "path": "/datasets/session_001",
      "version": "1.0.0",
      "total_images": 150,
      "total_annotations": 287,
      "reviewed": 45,
      "created": "2025-11-24T12:00:00"
    }
  ]
}
```

#### Get Dataset Details

```
GET /api/datasets/:id
```

**Response:**
```json
{
  "id": "session_001",
  "version": "1.0.0",
  "created": "2025-11-24T12:00:00",
  "total_images": 150,
  "total_annotations": 287,
  "categories": [
    {"id": 0, "name": "login_button", "count": 45},
    {"id": 1, "name": "submit_button", "count": 32}
  ],
  "statistics": {
    "reviewed": 45,
    "good": 40,
    "bad": 5,
    "pending": 105
  }
}
```

### Image Browsing

#### List Images

```
GET /api/datasets/:id/images?page=1&limit=20&filter=pending
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Images per page (default: 20)
- `filter`: Filter by status (all, pending, reviewed, good, bad)
- `category`: Filter by category name
- `state`: Filter by active state
- `confidence_min`: Minimum annotation confidence

**Response:**
```json
{
  "images": [
    {
      "id": "a1b2c3d4",
      "filename": "a1b2c3d4.png",
      "url": "/api/datasets/session_001/images/a1b2c3d4.png",
      "thumbnail_url": "/api/datasets/session_001/thumbnails/a1b2c3d4.jpg",
      "width": 1920,
      "height": 1080,
      "annotation_count": 3,
      "review_status": "pending",
      "action_type": "CLICK",
      "active_states": ["Login", "MainMenu"],
      "timestamp": 1700000000.0
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### Get Image Details

```
GET /api/datasets/:id/images/:image_id
```

**Response:**
```json
{
  "id": "a1b2c3d4",
  "filename": "a1b2c3d4.png",
  "url": "/api/datasets/session_001/images/a1b2c3d4.png",
  "width": 1920,
  "height": 1080,
  "annotations": [
    {
      "id": 0,
      "bbox": [100, 50, 200, 100],
      "category_id": 0,
      "category_name": "login_button",
      "confidence": 0.95,
      "source": "template_matching",
      "verified": false
    }
  ],
  "context": {
    "action_type": "CLICK",
    "active_states": ["Login"],
    "timestamp": 1700000000.0,
    "success": true
  },
  "review": {
    "status": "good",
    "notes": "Clear bounding box, accurate label",
    "reviewed_at": "2025-11-24T14:30:00"
  }
}
```

### Annotation Editing

#### Update Annotation

```
PUT /api/datasets/:id/images/:image_id/annotations/:ann_id
```

**Request Body:**
```json
{
  "bbox": [100, 50, 200, 100],
  "category_id": 0,
  "verified": true
}
```

**Response:**
```json
{
  "success": true,
  "annotation": {
    "id": 0,
    "bbox": [100, 50, 200, 100],
    "category_id": 0,
    "category_name": "login_button",
    "confidence": 0.95,
    "source": "template_matching",
    "verified": true
  }
}
```

#### Add Annotation

```
POST /api/datasets/:id/images/:image_id/annotations
```

**Request Body:**
```json
{
  "bbox": [150, 100, 80, 40],
  "category_id": 1,
  "confidence": 1.0,
  "source": "manual",
  "verified": true
}
```

**Response:**
```json
{
  "success": true,
  "annotation": {
    "id": 3,
    "bbox": [150, 100, 80, 40],
    "category_id": 1,
    "category_name": "submit_button",
    "confidence": 1.0,
    "source": "manual",
    "verified": true
  }
}
```

#### Delete Annotation

```
DELETE /api/datasets/:id/images/:image_id/annotations/:ann_id
```

**Response:**
```json
{
  "success": true
}
```

### Review Management

#### Submit Review

```
POST /api/datasets/:id/images/:image_id/review
```

**Request Body:**
```json
{
  "status": "good",
  "notes": "All annotations look correct"
}
```

**Response:**
```json
{
  "success": true,
  "review": {
    "status": "good",
    "notes": "All annotations look correct",
    "reviewed_at": "2025-11-24T14:30:00"
  }
}
```

#### Batch Review

```
POST /api/datasets/:id/batch-review
```

**Request Body:**
```json
{
  "image_ids": ["a1b2c3d4", "e5f6g7h8"],
  "status": "good"
}
```

**Response:**
```json
{
  "success": true,
  "updated": 2
}
```

### Export

#### Export Filtered Dataset

```
POST /api/datasets/:id/export
```

**Request Body:**
```json
{
  "output_dir": "/datasets/curated/v1.0.0",
  "filters": {
    "review_status": ["good"],
    "confidence_min": 0.8,
    "categories": ["login_button", "submit_button"]
  },
  "format": "coco"
}
```

**Response:**
```json
{
  "success": true,
  "export_id": "export_123",
  "status_url": "/api/exports/export_123"
}
```

#### Get Export Status

```
GET /api/exports/:export_id
```

**Response:**
```json
{
  "id": "export_123",
  "status": "completed",
  "progress": 100,
  "output_path": "/datasets/curated/v1.0.0",
  "images_exported": 85,
  "annotations_exported": 132
}
```

### Categories

#### List Categories

```
GET /api/datasets/:id/categories
```

**Response:**
```json
{
  "categories": [
    {
      "id": 0,
      "name": "login_button",
      "annotation_count": 45,
      "reviewed_count": 20
    },
    {
      "id": 1,
      "name": "submit_button",
      "annotation_count": 32,
      "reviewed_count": 15
    }
  ]
}
```

#### Update Category

```
PUT /api/datasets/:id/categories/:cat_id
```

**Request Body:**
```json
{
  "name": "login_btn"
}
```

**Response:**
```json
{
  "success": true,
  "category": {
    "id": 0,
    "name": "login_btn"
  }
}
```

### Statistics

#### Get Statistics

```
GET /api/datasets/:id/statistics
```

**Response:**
```json
{
  "overview": {
    "total_images": 150,
    "total_annotations": 287,
    "reviewed_images": 45,
    "pending_images": 105
  },
  "review_breakdown": {
    "good": 40,
    "bad": 5,
    "pending": 105
  },
  "category_breakdown": [
    {"category": "login_button", "count": 45, "avg_confidence": 0.92},
    {"category": "submit_button", "count": 32, "avg_confidence": 0.88}
  ],
  "confidence_distribution": {
    "0.0-0.5": 5,
    "0.5-0.7": 12,
    "0.7-0.9": 45,
    "0.9-1.0": 225
  },
  "source_breakdown": {
    "template_matching": 220,
    "user_click": 67
  }
}
```

## UI Components

### Main Interface

```
/datasets/:id
```

**Layout:**
- Header: Dataset name, version, statistics
- Sidebar: Filters, categories, review status
- Main: Image grid with thumbnails
- Detail Panel: Selected image with annotations

**Features:**
- Keyboard shortcuts (n/p for next/prev, g/b for review)
- Batch selection and review
- Search and filter
- Zoom and pan for detailed inspection

### Annotation Editor

```
/datasets/:id/images/:image_id/edit
```

**Features:**
- Canvas with image and bounding boxes
- Draw new boxes
- Resize and move existing boxes
- Change category labels
- Add/edit confidence scores
- Review status controls
- Context information (action type, states, timestamp)

### Dataset Dashboard

```
/datasets/:id/dashboard
```

**Features:**
- Statistics overview
- Charts (confidence distribution, category breakdown)
- Review progress
- Export options
- Quality metrics

## Implementation Notes

### Backend (Python/FastAPI)

```python
# api/datasets.py
from fastapi import FastAPI, HTTPException
from pathlib import Path
import json

app = FastAPI()

@app.get("/api/datasets/{dataset_id}/images/{image_id}")
async def get_image_details(dataset_id: str, image_id: str):
    dataset_dir = Path(f"/datasets/{dataset_id}")
    ann_file = dataset_dir / "annotations" / f"{image_id}.json"

    if not ann_file.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    with open(ann_file, 'r') as f:
        data = json.load(f)

    # Load review if exists
    reviews_file = dataset_dir / "reviews.jsonl"
    review = None
    if reviews_file.exists():
        with open(reviews_file, 'r') as f:
            for line in f:
                r = json.loads(line)
                if r["image_id"] == image_id:
                    review = r
                    break

    return {
        "id": image_id,
        "filename": data["image_filename"],
        "url": f"/api/datasets/{dataset_id}/images/{image_id}.png",
        "width": data["image_width"],
        "height": data["image_height"],
        "annotations": data["annotations"],
        "context": data["context"],
        "review": review
    }
```

### Frontend (React/Vue)

```jsx
// components/AnnotationEditor.jsx
import React, { useState } from 'react';
import { Stage, Layer, Image, Rect, Transformer } from 'react-konva';

export function AnnotationEditor({ imageData, annotations, onUpdate }) {
  const [selectedId, setSelectedId] = useState(null);

  const handleDragEnd = (e, annId) => {
    const newAnnotations = annotations.map(ann =>
      ann.id === annId
        ? { ...ann, bbox: [e.target.x(), e.target.y(), ann.bbox[2], ann.bbox[3]] }
        : ann
    );
    onUpdate(newAnnotations);
  };

  return (
    <Stage width={imageData.width} height={imageData.height}>
      <Layer>
        <Image image={imageData.image} />
        {annotations.map(ann => (
          <Rect
            key={ann.id}
            x={ann.bbox[0]}
            y={ann.bbox[1]}
            width={ann.bbox[2]}
            height={ann.bbox[3]}
            stroke={ann.verified ? 'green' : 'yellow'}
            strokeWidth={3}
            draggable
            onDragEnd={(e) => handleDragEnd(e, ann.id)}
            onClick={() => setSelectedId(ann.id)}
          />
        ))}
      </Layer>
    </Stage>
  );
}
```

## Future Enhancements

- Real-time collaboration (multiple annotators)
- Keyboard shortcuts and hotkeys
- Auto-save drafts
- Annotation templates (common patterns)
- Quality metrics (IoU, precision, recall)
- Integration with label versioning
- Import from other annotation formats
- ML-assisted annotation suggestions
- Annotation guidelines and documentation
- User management and permissions
