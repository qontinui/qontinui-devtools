# Detection Code Migration & State Detection Implementation Plan

## Executive Summary

This plan consolidates all detection algorithms into the qontinui library and implements a complete state detection pipeline with local processing capabilities. The migration enables cost-effective state analysis in qontinui-runner while maintaining optional cloud-based features in qontinui-web.

**Timeline:** 6-8 weeks
**Risk Level:** Medium (touching multiple repositories, API changes)
**Business Impact:** High (enables viable unit economics at $9-$24/month pricing)

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Target Architecture](#target-architecture)
3. [Migration Phases](#migration-phases)
4. [Implementation Details](#implementation-details)
5. [API Changes](#api-changes)
6. [Frontend Changes](#frontend-changes)
7. [Testing Strategy](#testing-strategy)
8. [Rollout Plan](#rollout-plan)
9. [Risk Mitigation](#risk-mitigation)

---

## Current State Analysis

### Code Distribution (Before Migration)

```
qontinui/src/qontinui/discovery/
├─ pixel_analysis/analyzers/
│  ├─ transition_detector.py              ✅ Already in library
│  └─ state_image_factory.py              ✅ Already in library

qontinui-web/backend/app/services/
├─ analysis/analyzers/
│  ├─ button_detector.py                  📦 MOVE to library
│  ├─ input_field_detector.py             📦 MOVE to library
│  ├─ icon_button_detector.py             📦 MOVE to library
│  ├─ dropdown_detector.py                📦 MOVE to library
│  ├─ modal_dialog_detector.py            📦 MOVE to library
│  ├─ sidebar_detector.py                 📦 MOVE to library
│  ├─ menu_bar_detector.py                📦 MOVE to library
│  ├─ typography_detector.py              📦 MOVE to library
│  ├─ button_*_detector.py (8 variants)   📦 MOVE to library
│  └─ graph_neural_detector.py            📦 MOVE to library
├─ region_analysis/analyzers/
│  ├─ grid_pattern_detector.py            📦 MOVE to library
│  ├─ window_border_detector.py           📦 MOVE to library
│  ├─ window_title_bar_detector.py        📦 MOVE to library
│  ├─ slot_border_detector.py             📦 MOVE to library
│  ├─ texture_uniformity_detector.py      📦 MOVE to library
│  ├─ *_text_detector.py (6 variants)     📦 MOVE to library
│  ├─ *_grid_detector.py (4 variants)     📦 MOVE to library
│  └─ corner_clustering_detector.py       📦 MOVE to library
└─ state_discovery_service.py             📦 MOVE core logic to library

qontinui-web/research_env/detectors/
├─ consistency_detector.py                📦 MOVE to library
├─ hybrid_detector.py                     📦 MOVE to library
├─ sam3_detector.py                       📦 MOVE to library
├─ edge_detector.py                       📦 MOVE to library
├─ contour_detector.py                    📦 MOVE to library
├─ mser_detector.py                       📦 MOVE to library
└─ color_detector.py                      📦 MOVE to library

NEW (To Implement):
├─ differential_consistency_detector.py   ✨ NEW in library
├─ state_builder.py                       ✨ NEW in library
├─ ocr_name_generator.py                  ✨ NEW in library
└─ element_identifier.py                  ✨ NEW in library
```

**Total Files to Migrate:** ~40 detector files
**New Features to Implement:** 4 core modules + integration

---

## Target Architecture

### qontinui Library Structure (After Migration)

```
qontinui/src/qontinui/
├─ discovery/
│  ├─ element_detection/              # GUI element detection
│  │  ├─ __init__.py
│  │  ├─ base_detector.py            # Base class for all detectors
│  │  ├─ button_detector.py          # From web backend
│  │  ├─ input_detector.py           # From web backend
│  │  ├─ icon_detector.py            # From web backend
│  │  ├─ dropdown_detector.py        # From web backend
│  │  ├─ modal_detector.py           # From web backend
│  │  ├─ sidebar_detector.py         # From web backend
│  │  ├─ menu_bar_detector.py        # From web backend
│  │  ├─ typography_detector.py      # From web backend
│  │  ├─ ensemble_detector.py        # Combines multiple detectors
│  │  └─ README.md
│  │
│  ├─ region_analysis/               # Region/structure detection
│  │  ├─ __init__.py
│  │  ├─ grid_detector.py            # From web backend
│  │  ├─ panel_detector.py           # From web backend
│  │  ├─ window_detector.py          # From web backend
│  │  ├─ text_region_detector.py     # From web backend
│  │  ├─ texture_detector.py         # From web backend
│  │  └─ README.md
│  │
│  ├─ state_detection/               # ✨ NEW: State detection
│  │  ├─ __init__.py
│  │  ├─ differential_consistency_detector.py  # ✨ NEW
│  │  ├─ consistency_detector.py     # From research_env
│  │  ├─ transition_detector.py      # Existing (refactored)
│  │  └─ README.md
│  │
│  ├─ state_construction/            # ✨ NEW: Build State objects
│  │  ├─ __init__.py
│  │  ├─ state_builder.py            # ✨ NEW: Core builder
│  │  ├─ ocr_name_generator.py       # ✨ NEW: OCR-based naming
│  │  ├─ element_identifier.py       # ✨ NEW: Identify StateImages/Regions/Locations
│  │  ├─ region_classifier.py        # ✨ NEW: Classify region types
│  │  ├─ click_point_analyzer.py     # ✨ NEW: Analyze StateLocations
│  │  └─ README.md
│  │
│  └─ experimental/                  # Cutting-edge/unstable
│     ├─ __init__.py
│     ├─ sam3_detector.py            # From research_env
│     ├─ hybrid_detector.py          # From research_env
│     ├─ graph_neural_detector.py    # From web backend
│     └─ README.md (clearly marked as experimental)
│
├─ model/state/                      # Existing state models
│  ├─ state.py                       # Already exists
│  ├─ state_image.py                 # Already exists
│  ├─ state_region.py                # Already exists
│  └─ state_location.py              # Already exists
│
└─ api/                              # Public API for library
   ├─ state_detection_api.py         # ✨ NEW: Simple API for state detection
   └─ element_detection_api.py       # ✨ NEW: Simple API for element detection
```

### Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     qontinui Library                         │
│  (Core detection algorithms, state construction)            │
└─────────────────────────────────────────────────────────────┘
           ▲                    ▲                    ▲
           │                    │                    │
     ┌─────┴─────┐        ┌─────┴─────┐       ┌─────┴─────┐
     │ qontinui- │        │ qontinui- │       │ qontinui- │
     │   runner  │        │    web    │       │    api    │
     │  (local)  │        │  (cloud)  │       │  (bridge) │
     └───────────┘        └───────────┘       └───────────┘
           │                    │                    │
           │                    │                    │
     ┌─────▼─────┐        ┌─────▼─────┐             │
     │  Electron │        │  Next.js  │             │
     │  Frontend │        │  Frontend │             │
     └───────────┘        └───────────┘             │
                                                     │
                              (Python bridge for external tools)
```

---

## Migration Phases

### Phase 1: Foundation (Week 1-2)

**Goal:** Set up new directory structure and move base classes

#### Tasks:
1. ✅ Create new directory structure in qontinui library
2. ✅ Create base classes and interfaces
3. ✅ Set up testing infrastructure
4. ✅ Create migration utilities

#### Deliverables:
- `qontinui/src/qontinui/discovery/element_detection/base_detector.py`
- `qontinui/src/qontinui/discovery/state_detection/__init__.py`
- `qontinui/src/qontinui/discovery/state_construction/__init__.py`
- Test suite templates
- Migration script for automated file movement

#### Files to Create:

**`qontinui/src/qontinui/discovery/base_detector.py`**
```python
"""Base class for all detection algorithms."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class BaseDetector(ABC):
    """Base class for detection algorithms."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def detect(self, image: np.ndarray, **params) -> List[Dict[str, Any]]:
        """
        Detect elements/regions in an image.

        Args:
            image: Input image as numpy array
            **params: Algorithm-specific parameters

        Returns:
            List of detections with bounding boxes and metadata
        """
        pass

    def get_param_grid(self) -> List[Dict[str, Any]]:
        """Return parameter grid for hyperparameter search."""
        return []
```

**`qontinui/src/qontinui/discovery/multi_screenshot_detector.py`**
```python
"""Base class for detectors that analyze multiple screenshots."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class MultiScreenshotDetector(ABC):
    """Base class for detectors analyzing screenshot sequences."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def detect_multi(
        self,
        screenshots: List[np.ndarray],
        **params
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Detect patterns across multiple screenshots.

        Args:
            screenshots: List of screenshots as numpy arrays
            **params: Algorithm-specific parameters

        Returns:
            Dict mapping screenshot index to list of detections
        """
        pass
```

---

### Phase 2: Core Algorithm Migration (Week 2-3)

**Goal:** Move existing detection algorithms to library

#### Tasks:
1. ✅ Move element detection algorithms
2. ✅ Move region analysis algorithms
3. ✅ Move experimental algorithms
4. ✅ Update imports in web backend
5. ✅ Deprecate old locations (with warnings)

#### Migration Priority:

**High Priority (Move First):**
- `consistency_detector.py` - Needed for new state detection
- `button_detector.py` - Most commonly used
- `grid_pattern_detector.py` - Core functionality
- `window_detector.py` - Core functionality

**Medium Priority:**
- All other element detectors
- All other region analyzers

**Low Priority (Can be done later):**
- Experimental detectors
- Specialized detectors

#### Migration Script:

**`scripts/migrate_detectors.py`**
```python
"""Automated migration script for detector files."""
import os
import shutil
import re
from pathlib import Path

MIGRATIONS = {
    # Source -> Destination
    'qontinui-web/backend/app/services/analysis/analyzers/button_detector.py':
        'qontinui/src/qontinui/discovery/element_detection/button_detector.py',

    'qontinui-web/backend/app/services/analysis/analyzers/input_field_detector.py':
        'qontinui/src/qontinui/discovery/element_detection/input_detector.py',

    'qontinui-web/research_env/detectors/consistency_detector.py':
        'qontinui/src/qontinui/discovery/state_detection/consistency_detector.py',

    # ... (add all 40 files)
}

def migrate_file(source: str, dest: str):
    """Migrate a single detector file."""
    source_path = Path(source)
    dest_path = Path(dest)

    # Read source
    with open(source_path, 'r') as f:
        content = f.read()

    # Update imports
    content = update_imports(content)

    # Create destination directory
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to destination
    with open(dest_path, 'w') as f:
        f.write(content)

    print(f"✅ Migrated {source_path.name} -> {dest_path}")

def update_imports(content: str) -> str:
    """Update import statements for new location."""
    # Update relative imports
    content = re.sub(
        r'from \.\.\.models import',
        'from qontinui.model import',
        content
    )

    # Add deprecation notice
    header = '''"""
MIGRATED FROM qontinui-web backend
This detector is now part of the qontinui core library.
"""

'''
    return header + content

if __name__ == '__main__':
    for source, dest in MIGRATIONS.items():
        migrate_file(source, dest)

    print(f"\n✅ Migrated {len(MIGRATIONS)} detector files")
```

---

### Phase 3: New State Detection Features (Week 3-5)

**Goal:** Implement new state detection algorithms and state construction

#### 3.1: Differential Consistency Detector

**`qontinui/src/qontinui/discovery/state_detection/differential_consistency_detector.py`**

```python
"""
Differential Consistency Detector

Identifies state regions by finding pixels that change consistently together
across multiple transitions to the same state.

Example: 1000 transitions to a menu state will show consistent pixel changes
in the menu region, while background pixels (game animation) change randomly.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2
from dataclasses import dataclass

from ..multi_screenshot_detector import MultiScreenshotDetector


@dataclass
class StateRegion:
    """A detected state region."""
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    consistency_score: float
    example_diff: np.ndarray  # Representative difference image


class DifferentialConsistencyDetector(MultiScreenshotDetector):
    """
    Detects state regions using differential consistency analysis.

    Key Insight: State boundaries have consistent change patterns across
    many examples, while dynamic backgrounds have inconsistent changes.
    """

    def __init__(self):
        super().__init__("DifferentialConsistencyDetector")

    def detect_state_regions(
        self,
        transition_pairs: List[Tuple[np.ndarray, np.ndarray]],
        consistency_threshold: float = 0.7,
        min_region_area: int = 500,
        **params
    ) -> List[StateRegion]:
        """
        Detect state regions from before/after screenshot pairs.

        Args:
            transition_pairs: List of (before, after) screenshot pairs
                             All pairs should represent transitions to the SAME state
            consistency_threshold: Minimum consistency score (0-1)
            min_region_area: Minimum pixel area for detected regions

        Returns:
            List of detected state regions with consistency scores
        """
        if len(transition_pairs) < 10:
            raise ValueError(
                f"Need at least 10 transition examples, got {len(transition_pairs)}. "
                f"More examples (100-1000) give better results."
            )

        # Step 1: Compute difference images for all transitions
        diff_images = self._compute_differences(transition_pairs)

        # Step 2: Analyze consistency across all differences
        consistency_map = self._compute_consistency(diff_images)

        # Step 3: Extract regions from consistency map
        regions = self._extract_regions(
            consistency_map,
            consistency_threshold,
            min_region_area
        )

        # Step 4: Score and rank regions
        scored_regions = self._score_regions(
            regions,
            consistency_map,
            diff_images
        )

        return scored_regions

    def _compute_differences(
        self,
        pairs: List[Tuple[np.ndarray, np.ndarray]]
    ) -> np.ndarray:
        """
        Compute difference images for all transition pairs.

        Returns:
            Array of shape (N, H, W) where N = number of pairs
        """
        diffs = []

        for before, after in pairs:
            # Ensure same size
            if before.shape != after.shape:
                after = cv2.resize(after, (before.shape[1], before.shape[0]))

            # Convert to grayscale if needed
            if len(before.shape) == 3:
                before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
            if len(after.shape) == 3:
                after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

            # Compute absolute difference
            diff = cv2.absdiff(before, after).astype(np.float32)
            diffs.append(diff)

        return np.stack(diffs, axis=0)

    def _compute_consistency(self, diff_images: np.ndarray) -> np.ndarray:
        """
        Compute consistency score for each pixel across all differences.

        High consistency = pixel changes similarly across all examples
        Low consistency = pixel changes randomly

        Returns:
            Consistency map (H, W) with scores 0-1
        """
        # Compute mean and std of differences at each pixel
        mean_diff = np.mean(diff_images, axis=0)
        std_diff = np.std(diff_images, axis=0)

        # Consistency score: high mean + low std = consistent change
        # Avoid division by zero
        consistency = mean_diff / (std_diff + 1.0)

        # Normalize to 0-1
        consistency = cv2.normalize(
            consistency,
            None,
            0,
            1,
            cv2.NORM_MINMAX
        )

        return consistency.astype(np.float32)

    def _extract_regions(
        self,
        consistency_map: np.ndarray,
        threshold: float,
        min_area: int
    ) -> List[Tuple[int, int, int, int]]:
        """
        Extract connected regions from consistency map.

        Returns:
            List of bounding boxes (x, y, w, h)
        """
        # Threshold consistency map
        mask = (consistency_map >= threshold).astype(np.uint8) * 255

        # Clean up with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract bounding boxes
        bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            if area >= min_area:
                bboxes.append((x, y, w, h))

        return bboxes

    def _score_regions(
        self,
        bboxes: List[Tuple[int, int, int, int]],
        consistency_map: np.ndarray,
        diff_images: np.ndarray
    ) -> List[StateRegion]:
        """
        Score regions by average consistency within bbox.

        Returns:
            List of StateRegion objects sorted by score (descending)
        """
        regions = []

        for bbox in bboxes:
            x, y, w, h = bbox

            # Extract consistency values in this region
            region_consistency = consistency_map[y:y+h, x:x+w]
            avg_consistency = np.mean(region_consistency)

            # Get representative difference image
            median_diff = np.median(diff_images[:, y:y+h, x:x+w], axis=0)

            regions.append(StateRegion(
                bbox=bbox,
                consistency_score=float(avg_consistency),
                example_diff=median_diff
            ))

        # Sort by consistency score (highest first)
        regions.sort(key=lambda r: r.consistency_score, reverse=True)

        return regions

    def visualize_consistency(
        self,
        consistency_map: np.ndarray,
        regions: List[StateRegion],
        screenshot: np.ndarray
    ) -> np.ndarray:
        """
        Create visualization of detected regions overlaid on screenshot.

        Returns:
            Visualization image
        """
        # Create heatmap
        heatmap = cv2.applyColorMap(
            (consistency_map * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )

        # Overlay on screenshot
        if len(screenshot.shape) == 2:
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)

        overlay = cv2.addWeighted(screenshot, 0.6, heatmap, 0.4, 0)

        # Draw region bounding boxes
        for region in regions:
            x, y, w, h = region.bbox
            color = (0, 255, 0)  # Green
            thickness = 2

            cv2.rectangle(overlay, (x, y), (x+w, y+h), color, thickness)

            # Add consistency score label
            label = f"{region.consistency_score:.2f}"
            cv2.putText(
                overlay,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        return overlay
```

#### 3.2: OCR Name Generator

**`qontinui/src/qontinui/discovery/state_construction/ocr_name_generator.py`**

```python
"""
OCR-based Name Generator

Generates meaningful names for states, images, and regions using OCR
and semantic analysis.
"""

from typing import Optional, List, Dict
import re
import numpy as np

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


class OCRNameGenerator:
    """Generates names using OCR text extraction."""

    def __init__(self, engine: str = 'auto'):
        """
        Initialize OCR engine.

        Args:
            engine: 'tesseract', 'easyocr', or 'auto' (tries both)
        """
        self.engine = engine
        self.reader = None

        if engine == 'easyocr' or (engine == 'auto' and HAS_EASYOCR):
            self.reader = easyocr.Reader(['en'])
            self.engine = 'easyocr'
        elif engine == 'tesseract' or (engine == 'auto' and HAS_TESSERACT):
            self.engine = 'tesseract'
        else:
            raise ValueError(
                "No OCR engine available. Install pytesseract or easyocr."
            )

    def generate_name_from_image(
        self,
        image: np.ndarray,
        context: str = 'generic'
    ) -> str:
        """
        Generate a name from an image using OCR.

        Args:
            image: Image as numpy array
            context: Context hint ('title_bar', 'button', 'panel', etc.)

        Returns:
            Generated name (sanitized, lowercase, underscores)
        """
        # Extract text
        text = self._extract_text(image)

        if text:
            # Clean and format
            name = self._sanitize_text(text)

            # Add context prefix if no meaningful text
            if len(name) < 3:
                name = f"{context}_{name}" if name else context

            return name

        # Fallback to position-based name
        return self._generate_fallback_name(image, context)

    def generate_state_name(
        self,
        screenshot: np.ndarray,
        detected_text_regions: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a name for a state from a screenshot.

        Looks for:
        1. Title bar text (top of screen)
        2. Prominent headings
        3. Modal dialog titles
        4. Fallback to generic name

        Args:
            screenshot: Full screenshot
            detected_text_regions: Optional pre-detected text regions

        Returns:
            State name
        """
        h, w = screenshot.shape[:2]

        # Strategy 1: Check title bar region (top 10% of screen)
        title_bar = screenshot[:int(h * 0.1), :]
        title_text = self._extract_text(title_bar)

        if title_text and len(title_text) > 3:
            return self._sanitize_text(title_text)

        # Strategy 2: Look for large text near top
        top_third = screenshot[:int(h * 0.33), :]
        prominent_text = self._extract_prominent_text(top_third)

        if prominent_text:
            return self._sanitize_text(prominent_text)

        # Strategy 3: Use detected text regions if provided
        if detected_text_regions:
            # Find largest text region near top
            top_regions = [
                r for r in detected_text_regions
                if r['y'] < h * 0.5
            ]

            if top_regions:
                largest = max(top_regions, key=lambda r: r['area'])
                text = largest.get('text', '')
                if text:
                    return self._sanitize_text(text)

        # Fallback: generic name based on screenshot hash
        return f"state_{hash(screenshot.tobytes()) % 10000}"

    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text from image using configured OCR engine."""
        if self.engine == 'easyocr':
            results = self.reader.readtext(image)
            # Combine all detected text
            text = ' '.join([r[1] for r in results])
            return text.strip()

        elif self.engine == 'tesseract':
            if HAS_TESSERACT:
                text = pytesseract.image_to_string(image)
                return text.strip()

        return ''

    def _extract_prominent_text(self, image: np.ndarray) -> str:
        """
        Extract the most prominent (largest) text from image.

        Uses text size detection to find headings/titles.
        """
        if self.engine == 'easyocr':
            results = self.reader.readtext(image)

            if not results:
                return ''

            # Score by bounding box area (larger = more prominent)
            def score_result(r):
                bbox = r[0]
                # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                width = bbox[1][0] - bbox[0][0]
                height = bbox[2][1] - bbox[1][1]
                return width * height

            best = max(results, key=score_result)
            return best[1].strip()

        else:
            # Tesseract fallback: just get first line
            text = self._extract_text(image)
            lines = text.split('\n')
            return lines[0] if lines else ''

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text to valid identifier name.

        - Lowercase
        - Replace spaces with underscores
        - Remove special characters
        - Truncate to reasonable length
        """
        # Lowercase
        text = text.lower()

        # Replace spaces and common separators with underscores
        text = re.sub(r'[\s\-./\\]+', '_', text)

        # Remove special characters (keep alphanumeric and underscores)
        text = re.sub(r'[^a-z0-9_]', '', text)

        # Remove consecutive underscores
        text = re.sub(r'_+', '_', text)

        # Strip leading/trailing underscores
        text = text.strip('_')

        # Truncate to 50 characters
        if len(text) > 50:
            text = text[:50].rsplit('_', 1)[0]  # Break at word boundary

        return text or 'unnamed'

    def _generate_fallback_name(
        self,
        image: np.ndarray,
        context: str
    ) -> str:
        """Generate fallback name when OCR fails."""
        # Use image hash for uniqueness
        img_hash = hash(image.tobytes()) % 1000
        return f"{context}_{img_hash}"
```

#### 3.3: State Builder

**`qontinui/src/qontinui/discovery/state_construction/state_builder.py`**

```python
"""
State Builder

Constructs holistic State objects with StateImages, StateRegions, and
StateLocations, all with meaningful names.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2
from dataclasses import dataclass

from ...model.state.state import State
from ...model.state.state_image import StateImage
from ...model.state.state_region import StateRegion
from ...model.state.state_location import StateLocation

from ..state_detection.consistency_detector import ConsistencyDetector
from ..state_detection.differential_consistency_detector import (
    DifferentialConsistencyDetector
)
from .ocr_name_generator import OCRNameGenerator
from .element_identifier import ElementIdentifier


@dataclass
class TransitionInfo:
    """Information about a transition."""
    before_screenshot: np.ndarray
    after_screenshot: np.ndarray
    click_point: Optional[Tuple[int, int]]
    input_events: List[Dict[str, Any]]
    target_state_name: Optional[str] = None


class StateBuilder:
    """
    Builds complete State objects from screenshot sequences.

    Creates holistic states with:
    - Meaningful names (from OCR)
    - StateImages (persistent visual elements)
    - StateRegions (functional areas)
    - StateLocations (effective click points)
    """

    def __init__(self):
        self.consistency_detector = ConsistencyDetector()
        self.diff_detector = DifferentialConsistencyDetector()
        self.name_generator = OCRNameGenerator()
        self.element_identifier = ElementIdentifier()

    def build_state_from_screenshots(
        self,
        screenshot_sequence: List[np.ndarray],
        transitions_to_state: Optional[List[TransitionInfo]] = None,
        transitions_from_state: Optional[List[TransitionInfo]] = None
    ) -> State:
        """
        Build a complete State object from screenshot data.

        Args:
            screenshot_sequence: Screenshots where this state is active
            transitions_to_state: Transitions leading TO this state
            transitions_from_state: Transitions leading FROM this state

        Returns:
            Fully constructed State object with all components
        """
        # 1. Generate state name
        state_name = self._generate_state_name(
            screenshot_sequence,
            transitions_to_state
        )

        # 2. Identify StateImages (persistent elements)
        state_images = self._identify_state_images(screenshot_sequence)

        # 3. Identify StateRegions (functional areas)
        state_regions = self._identify_state_regions(screenshot_sequence)

        # 4. Identify StateLocations (click points)
        state_locations = self._identify_state_locations(
            transitions_from_state
        )

        # 5. Determine state boundaries (if from transitions)
        state_boundary = None
        if transitions_to_state and len(transitions_to_state) >= 10:
            state_boundary = self._determine_state_boundary(
                transitions_to_state
            )

        return State(
            name=state_name,
            state_images=state_images,
            state_regions=state_regions,
            state_locations=state_locations,
            boundary_bbox=state_boundary
        )

    def _generate_state_name(
        self,
        screenshots: List[np.ndarray],
        transitions: Optional[List[TransitionInfo]]
    ) -> str:
        """Generate meaningful name for the state."""
        # Use first screenshot as representative
        representative = screenshots[0]

        # Extract name using OCR
        return self.name_generator.generate_state_name(representative)

    def _identify_state_images(
        self,
        screenshots: List[np.ndarray]
    ) -> List[StateImage]:
        """
        Identify StateImages - persistent visual elements.

        Examples: title bars, icons, headers, logos
        """
        if len(screenshots) < 2:
            return []

        # Use consistency detector to find persistent elements
        consistent_regions = self.consistency_detector.detect_multi(
            screenshots,
            consistency_threshold=0.9,
            min_area=100
        )

        # Convert to StateImages
        state_images = []

        for region in consistent_regions:
            bbox = region['bbox']
            x, y, w, h = bbox

            # Extract image
            img = screenshots[0][y:y+h, x:x+w].copy()

            # Generate name
            name = self.name_generator.generate_name_from_image(
                img,
                context=self._classify_image_context(bbox, screenshots[0])
            )

            state_images.append(StateImage(
                name=name,
                image_data=img,
                search_area=None,  # Full screen
                x=x,
                y=y,
                w=w,
                h=h
            ))

        return state_images

    def _classify_image_context(
        self,
        bbox: Tuple[int, int, int, int],
        screenshot: np.ndarray
    ) -> str:
        """Classify what type of element this might be based on position."""
        x, y, w, h = bbox
        img_h, img_w = screenshot.shape[:2]

        # Title bar: top 10%, wide
        if y < img_h * 0.1 and w > img_w * 0.3:
            return 'title_bar'

        # Icon: small, squarish
        if w < 100 and h < 100 and 0.5 < w/h < 2.0:
            return 'icon'

        # Button: medium size
        if 50 < w < 300 and 20 < h < 80:
            return 'button'

        # Header: top third, wide
        if y < img_h * 0.33 and w > img_w * 0.5:
            return 'header'

        return 'element'

    def _identify_state_regions(
        self,
        screenshots: List[np.ndarray]
    ) -> List[StateRegion]:
        """
        Identify StateRegions - functional areas.

        Examples: inventory grids, character panels, skill bars
        """
        regions = []

        # Use element identifier to find structured regions
        detected = self.element_identifier.identify_regions(screenshots)

        for region_info in detected:
            bbox = region_info['bbox']
            region_type = region_info['type']

            # Generate name
            name = self._generate_region_name(region_info, screenshots[0])

            regions.append(StateRegion(
                name=name,
                x=bbox[0],
                y=bbox[1],
                w=bbox[2],
                h=bbox[3],
                region_type=region_type
            ))

        return regions

    def _generate_region_name(
        self,
        region_info: Dict,
        screenshot: np.ndarray
    ) -> str:
        """Generate name for a region."""
        region_type = region_info['type']
        bbox = region_info['bbox']

        # Try OCR first
        x, y, w, h = bbox
        region_img = screenshot[y:y+h, x:x+w]
        ocr_name = self.name_generator.generate_name_from_image(
            region_img,
            context=region_type
        )

        # If OCR gives meaningful name, use it
        if len(ocr_name) > len(region_type) + 5:
            return ocr_name

        # Otherwise use type + position
        return f"{region_type}_{x}_{y}"

    def _identify_state_locations(
        self,
        transitions: Optional[List[TransitionInfo]]
    ) -> List[StateLocation]:
        """
        Identify StateLocations - effective click points.

        Clusters click points that lead to same transitions.
        """
        if not transitions:
            return []

        # Group transitions by target state
        by_target: Dict[str, List[TransitionInfo]] = {}
        for trans in transitions:
            target = trans.target_state_name or 'unknown'
            if target not in by_target:
                by_target[target] = []
            by_target[target].append(trans)

        locations = []

        for target_state, trans_list in by_target.items():
            # Extract click points
            click_points = [
                t.click_point for t in trans_list
                if t.click_point is not None
            ]

            if not click_points:
                continue

            # Compute centroid
            centroid = np.mean(click_points, axis=0).astype(int)

            # Compute consistency (std deviation)
            std = np.std(click_points, axis=0)
            consistency = 1.0 / (1.0 + np.mean(std))  # 0-1 score

            locations.append(StateLocation(
                name=f"click_to_{target_state}",
                x=int(centroid[0]),
                y=int(centroid[1]),
                target_state=target_state,
                confidence=float(consistency)
            ))

        return locations

    def _determine_state_boundary(
        self,
        transitions: List[TransitionInfo]
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Determine bounding box of state using differential consistency.

        Useful for modal dialogs, popup windows, etc.
        """
        # Create transition pairs
        pairs = [
            (t.before_screenshot, t.after_screenshot)
            for t in transitions
        ]

        # Detect state regions
        regions = self.diff_detector.detect_state_regions(
            pairs,
            consistency_threshold=0.7,
            min_region_area=500
        )

        if not regions:
            return None

        # Return largest region as state boundary
        largest = max(regions, key=lambda r: r.bbox[2] * r.bbox[3])
        return largest.bbox
```

(Continuing in next section due to length...)

---

### Phase 4: API Updates (Week 5)

**Goal:** Update qontinui-api to expose state detection functionality

#### 4.1: New API Endpoints

**`qontinui-api/state_discovery_api.py` (Update)**

```python
"""
State Discovery API

Provides endpoints for state detection and analysis.
Now delegates to qontinui library instead of implementing algorithms.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import numpy as np
import cv2
from pathlib import Path

# Import from qontinui library
from qontinui.discovery.state_detection.differential_consistency_detector import (
    DifferentialConsistencyDetector
)
from qontinui.discovery.state_construction.state_builder import (
    StateBuilder,
    TransitionInfo
)

router = APIRouter()

# Initialize detectors
diff_detector = DifferentialConsistencyDetector()
state_builder = StateBuilder()


@router.post("/api/v1/state-detection/analyze-transitions")
async def analyze_transitions(
    screenshot_files: List[UploadFile] = File(...),
    transition_metadata: str = Form(...)  # JSON string
):
    """
    Analyze transitions and build state structure.

    Expects pairs of before/after screenshots with metadata about
    click points and input events.
    """
    # Parse metadata
    import json
    metadata = json.loads(transition_metadata)

    # Load screenshots
    screenshots = []
    for file in screenshot_files:
        img_bytes = await file.read()
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        screenshots.append(img)

    # Group into transition pairs
    transitions = []
    for i in range(0, len(screenshots) - 1, 2):
        trans_info = TransitionInfo(
            before_screenshot=screenshots[i],
            after_screenshot=screenshots[i + 1],
            click_point=tuple(metadata[i]['click_point']) if 'click_point' in metadata[i] else None,
            input_events=metadata[i].get('input_events', [])
        )
        transitions.append(trans_info)

    # Build state using library
    state = state_builder.build_state_from_screenshots(
        screenshot_sequence=[t.after_screenshot for t in transitions],
        transitions_to_state=transitions
    )

    # Serialize state to JSON
    return {
        'state': {
            'name': state.name,
            'state_images': [
                {
                    'name': img.name,
                    'bbox': (img.x, img.y, img.w, img.h)
                }
                for img in state.state_images
            ],
            'state_regions': [
                {
                    'name': region.name,
                    'bbox': (region.x, region.y, region.w, region.h),
                    'type': region.region_type
                }
                for region in state.state_regions
            ],
            'state_locations': [
                {
                    'name': loc.name,
                    'position': (loc.x, loc.y),
                    'target_state': loc.target_state
                }
                for loc in state.state_locations
            ]
        }
    }


@router.post("/api/v1/state-detection/detect-regions")
async def detect_state_regions(
    before_screenshots: List[UploadFile] = File(...),
    after_screenshots: List[UploadFile] = File(...),
    consistency_threshold: float = Form(0.7),
    min_area: int = Form(500)
):
    """
    Detect state regions using differential consistency.

    Lightweight endpoint for just region detection without full state building.
    """
    # Load screenshots
    before_imgs = [load_image(await f.read()) for f in before_screenshots]
    after_imgs = [load_image(await f.read()) for f in after_screenshots]

    # Create pairs
    pairs = list(zip(before_imgs, after_imgs))

    # Detect regions using library
    regions = diff_detector.detect_state_regions(
        pairs,
        consistency_threshold=consistency_threshold,
        min_region_area=min_area
    )

    return {
        'regions': [
            {
                'bbox': region.bbox,
                'consistency_score': region.consistency_score
            }
            for region in regions
        ]
    }


def load_image(img_bytes: bytes) -> np.ndarray:
    """Load image from bytes."""
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
```

---

### Phase 5: Runner Integration (Week 5-6)

**Goal:** Enable local state detection in qontinui-runner

#### 5.1: Python Bridge Service

**`qontinui-runner/python-bridge/services/state_detection_service.py`**

```python
"""
State Detection Service for qontinui-runner

Orchestrates local state detection using qontinui library.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import cv2

# Add qontinui library to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'qontinui' / 'src'))

from qontinui.discovery.state_construction.state_builder import (
    StateBuilder,
    TransitionInfo
)
from qontinui.discovery.state_detection.differential_consistency_detector import (
    DifferentialConsistencyDetector
)


class LocalStateDetectionService:
    """
    Service for local state detection.

    Processes captured screenshots and builds state structure
    entirely locally (no cloud costs).
    """

    def __init__(self):
        self.state_builder = StateBuilder()
        self.diff_detector = DifferentialConsistencyDetector()

    def process_capture_session(
        self,
        screenshots_dir: Path,
        input_events_file: Path,
        output_file: Path
    ) -> Dict[str, Any]:
        """
        Process a capture session and generate state structure.

        Args:
            screenshots_dir: Directory containing captured screenshots
            input_events_file: JSON file with input events
            output_file: Where to save state structure JSON

        Returns:
            Summary of detection results
        """
        # Load screenshots
        screenshots = self._load_screenshots(screenshots_dir)

        # Load input events
        with open(input_events_file, 'r') as f:
            input_events = json.load(f)

        # Group into transitions
        transitions = self._group_into_transitions(
            screenshots,
            input_events
        )

        # Build states
        states = []
        for state_transitions in transitions.values():
            state = self.state_builder.build_state_from_screenshots(
                screenshot_sequence=[t.after_screenshot for t in state_transitions],
                transitions_to_state=state_transitions
            )
            states.append(state)

        # Serialize to JSON
        state_structure = self._serialize_states(states)

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(state_structure, f, indent=2)

        return {
            'total_screenshots': len(screenshots),
            'total_states': len(states),
            'output_file': str(output_file),
            'summary': state_structure
        }

    def _load_screenshots(self, screenshots_dir: Path) -> List[np.ndarray]:
        """Load all screenshots from directory."""
        screenshot_files = sorted(screenshots_dir.glob('*.png'))

        screenshots = []
        for file in screenshot_files:
            img = cv2.imread(str(file))
            if img is not None:
                screenshots.append(img)

        return screenshots

    def _group_into_transitions(
        self,
        screenshots: List[np.ndarray],
        input_events: List[Dict]
    ) -> Dict[str, List[TransitionInfo]]:
        """
        Group screenshots into transitions based on input events.

        Uses timing and clustering to identify state boundaries.
        """
        # Simple implementation: group by time gaps
        # TODO: Use more sophisticated clustering

        transitions_by_state = {}
        current_state = 'state_0'

        for i in range(len(screenshots) - 1):
            # Find input events between this screenshot and next
            relevant_events = [
                e for e in input_events
                if i <= e.get('screenshot_index', -1) < i + 1
            ]

            # Create transition
            trans = TransitionInfo(
                before_screenshot=screenshots[i],
                after_screenshot=screenshots[i + 1],
                click_point=self._extract_click_point(relevant_events),
                input_events=relevant_events
            )

            if current_state not in transitions_by_state:
                transitions_by_state[current_state] = []

            transitions_by_state[current_state].append(trans)

        return transitions_by_state

    def _extract_click_point(
        self,
        events: List[Dict]
    ) -> tuple[int, int] | None:
        """Extract click point from events."""
        for event in events:
            if event.get('type') == 'mousedown':
                return (event['x'], event['y'])
        return None

    def _serialize_states(self, states: List[Any]) -> Dict[str, Any]:
        """Serialize states to JSON-compatible dict."""
        return {
            'states': [
                {
                    'name': state.name,
                    'state_images': [
                        {
                            'name': img.name,
                            'bbox': [img.x, img.y, img.w, img.h]
                        }
                        for img in state.state_images
                    ],
                    'state_regions': [
                        {
                            'name': region.name,
                            'bbox': [region.x, region.y, region.w, region.h],
                            'type': region.region_type
                        }
                        for region in state.state_regions
                    ],
                    'state_locations': [
                        {
                            'name': loc.name,
                            'position': [loc.x, loc.y],
                            'target_state': loc.target_state
                        }
                        for loc in state.state_locations
                    ]
                }
                for state in states
            ]
        }


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python state_detection_service.py <screenshots_dir> <input_events.json> <output.json>")
        sys.exit(1)

    service = LocalStateDetectionService()
    result = service.process_capture_session(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        Path(sys.argv[3])
    )

    print(f"✅ Processed {result['total_screenshots']} screenshots")
    print(f"✅ Detected {result['total_states']} states")
    print(f"✅ Output saved to {result['output_file']}")
```

#### 5.2: TypeScript Integration

**`qontinui-runner/src/services/StateDetectionService.ts`**

```typescript
/**
 * State Detection Service
 *
 * Manages local state detection by calling Python bridge.
 */

import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export interface StateDetectionResult {
  totalScreenshots: number;
  totalStates: number;
  states: DetectedState[];
}

export interface DetectedState {
  name: string;
  stateImages: StateImageInfo[];
  stateRegions: StateRegionInfo[];
  stateLocations: StateLocationInfo[];
}

export interface StateImageInfo {
  name: string;
  bbox: [number, number, number, number];
}

export interface StateRegionInfo {
  name: string;
  bbox: [number, number, number, number];
  type: string;
}

export interface StateLocationInfo {
  name: string;
  position: [number, number];
  targetState: string;
}

export class StateDetectionService {
  private pythonBridgePath: string;

  constructor() {
    this.pythonBridgePath = path.join(
      __dirname,
      '../../python-bridge/services/state_detection_service.py'
    );
  }

  /**
   * Process a capture session and detect states locally.
   */
  async processSession(
    screenshotsDir: string,
    inputEventsFile: string,
    outputFile: string
  ): Promise<StateDetectionResult> {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [
        this.pythonBridgePath,
        screenshotsDir,
        inputEventsFile,
        outputFile
      ]);

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process failed: ${stderr}`));
          return;
        }

        // Read output file
        const resultJson = fs.readFileSync(outputFile, 'utf-8');
        const result = JSON.parse(resultJson);

        resolve({
          totalScreenshots: result.states.length * 10, // Estimate
          totalStates: result.states.length,
          states: result.states.map(this.parseState)
        });
      });
    });
  }

  private parseState(rawState: any): DetectedState {
    return {
      name: rawState.name,
      stateImages: rawState.state_images,
      stateRegions: rawState.state_regions,
      stateLocations: rawState.state_locations
    };
  }
}
```

---

### Phase 6: Frontend Development (Week 6-7)

#### 6.1: Runner Frontend - State Viewer

**`qontinui-runner/src/components/StateViewer.tsx`**

```typescript
/**
 * State Viewer Component
 *
 * Displays detected states with visualization.
 */

import React, { useState } from 'react';
import { DetectedState } from '../services/StateDetectionService';

interface StateViewerProps {
  states: DetectedState[];
  onStateEdit: (state: DetectedState) => void;
  onExport: () => void;
}

export const StateViewer: React.FC<StateViewerProps> = ({
  states,
  onStateEdit,
  onExport
}) => {
  const [selectedState, setSelectedState] = useState<DetectedState | null>(null);

  return (
    <div className="state-viewer">
      <div className="state-list">
        <h2>Detected States ({states.length})</h2>

        {states.map((state, index) => (
          <div
            key={index}
            className={`state-item ${selectedState === state ? 'selected' : ''}`}
            onClick={() => setSelectedState(state)}
          >
            <h3>{state.name}</h3>
            <div className="state-stats">
              <span>{state.stateImages.length} images</span>
              <span>{state.stateRegions.length} regions</span>
              <span>{state.stateLocations.length} locations</span>
            </div>
          </div>
        ))}
      </div>

      {selectedState && (
        <div className="state-detail">
          <h2>{selectedState.name}</h2>

          <section>
            <h3>State Images</h3>
            {selectedState.stateImages.map((img, i) => (
              <div key={i} className="image-item">
                <span>{img.name}</span>
                <span className="bbox">
                  {img.bbox[0]}, {img.bbox[1]} - {img.bbox[2]}x{img.bbox[3]}
                </span>
              </div>
            ))}
          </section>

          <section>
            <h3>State Regions</h3>
            {selectedState.stateRegions.map((region, i) => (
              <div key={i} className="region-item">
                <span>{region.name}</span>
                <span className="type">{region.type}</span>
              </div>
            ))}
          </section>

          <section>
            <h3>State Locations</h3>
            {selectedState.stateLocations.map((loc, i) => (
              <div key={i} className="location-item">
                <span>{loc.name}</span>
                <span>→ {loc.targetState}</span>
              </div>
            ))}
          </section>

          <div className="actions">
            <button onClick={() => onStateEdit(selectedState)}>
              Edit State
            </button>
            <button onClick={onExport}>
              Export to Web
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

#### 6.2: Web Frontend - State Manager

**`qontinui-web/frontend/src/components/state-detection-viewer.tsx`**

```typescript
/**
 * State Detection Viewer for qontinui-web
 *
 * Visualizes and manages detected states with editing capabilities.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface DetectedState {
  name: string;
  stateImages: StateImage[];
  stateRegions: StateRegion[];
  stateLocations: StateLocation[];
  screenshot?: string; // Base64 encoded
}

interface StateImage {
  name: string;
  bbox: [number, number, number, number];
  imageData?: string; // Base64 encoded
}

interface StateRegion {
  name: string;
  bbox: [number, number, number, number];
  type: string;
}

interface StateLocation {
  name: string;
  position: [number, number];
  targetState: string;
  confidence?: number;
}

export function StateDetectionViewer() {
  const [states, setStates] = useState<DetectedState[]>([]);
  const [selectedState, setSelectedState] = useState<DetectedState | null>(null);
  const [editing, setEditing] = useState(false);

  // Load states from API
  useEffect(() => {
    loadStates();
  }, []);

  const loadStates = async () => {
    const response = await fetch('/api/v1/state-detection/states');
    const data = await response.json();
    setStates(data.states);
  };

  const handleRename = async (state: DetectedState, newName: string) => {
    // Update state name
    const updated = { ...state, name: newName };

    // Save to backend
    await fetch(`/api/v1/state-detection/states/${state.name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });

    // Refresh
    loadStates();
  };

  const handleExport = async (state: DetectedState) => {
    // Export to automation project
    await fetch('/api/v1/automation/import-state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state)
    });

    alert(`Exported ${state.name} to automation project`);
  };

  return (
    <div className="grid grid-cols-3 gap-4 p-4">
      {/* State List */}
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle>Detected States ({states.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {states.map((state, index) => (
              <div
                key={index}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedState === state ? 'bg-blue-50 border-blue-500' : ''
                }`}
                onClick={() => setSelectedState(state)}
              >
                <div className="font-semibold">{state.name}</div>
                <div className="text-sm text-gray-600">
                  {state.stateImages.length} images · {state.stateRegions.length} regions
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* State Detail */}
      {selectedState && (
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>{selectedState.name}</span>
              <div className="space-x-2">
                <Button onClick={() => setEditing(!editing)}>
                  {editing ? 'Save' : 'Edit'}
                </Button>
                <Button onClick={() => handleExport(selectedState)}>
                  Export
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Screenshot Visualization */}
            {selectedState.screenshot && (
              <div className="mb-4">
                <img
                  src={selectedState.screenshot}
                  alt="State screenshot"
                  className="w-full border rounded"
                />
              </div>
            )}

            {/* State Images */}
            <div className="mb-4">
              <h3 className="font-semibold mb-2">State Images</h3>
              <div className="space-y-2">
                {selectedState.stateImages.map((img, i) => (
                  <div key={i} className="flex items-center justify-between p-2 border rounded">
                    {editing ? (
                      <Input
                        defaultValue={img.name}
                        onBlur={(e) => {
                          // Update name
                          img.name = e.target.value;
                        }}
                      />
                    ) : (
                      <span>{img.name}</span>
                    )}
                    <span className="text-sm text-gray-600">
                      {img.bbox.join(', ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* State Regions */}
            <div className="mb-4">
              <h3 className="font-semibold mb-2">State Regions</h3>
              <div className="space-y-2">
                {selectedState.stateRegions.map((region, i) => (
                  <div key={i} className="flex items-center justify-between p-2 border rounded">
                    <span>{region.name}</span>
                    <span className="text-sm bg-blue-100 px-2 py-1 rounded">
                      {region.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* State Locations */}
            <div>
              <h3 className="font-semibold mb-2">State Locations</h3>
              <div className="space-y-2">
                {selectedState.stateLocations.map((loc, i) => (
                  <div key={i} className="flex items-center justify-between p-2 border rounded">
                    <span>{loc.name}</span>
                    <span className="text-sm text-gray-600">
                      → {loc.targetState}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

---

### Phase 7: Testing & Validation (Week 7-8)

**Goal:** Comprehensive testing of migration and new features

#### 7.1: Unit Tests

**`qontinui/tests/discovery/state_detection/test_differential_consistency.py`**

```python
"""Tests for Differential Consistency Detector."""

import pytest
import numpy as np
import cv2

from qontinui.discovery.state_detection.differential_consistency_detector import (
    DifferentialConsistencyDetector,
    StateRegion
)


class TestDifferentialConsistencyDetector:
    """Test suite for differential consistency detection."""

    @pytest.fixture
    def detector(self):
        return DifferentialConsistencyDetector()

    @pytest.fixture
    def synthetic_menu_transitions(self):
        """
        Generate synthetic transitions with a consistent menu region.

        Creates 100 before/after pairs where:
        - Menu appears at (100, 100) with size (200, 300)
        - Background has random noise
        """
        transitions = []

        for _ in range(100):
            # Create before image (no menu, random background)
            before = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

            # Create after image (with menu)
            after = before.copy()

            # Add menu (consistent location and appearance)
            menu_color = (200, 200, 200)  # Gray menu
            after[100:400, 100:300] = menu_color

            # Add some noise to background
            noise = np.random.randint(-20, 20, before.shape, dtype=np.int16)
            after = np.clip(after.astype(np.int16) + noise, 0, 255).astype(np.uint8)

            transitions.append((before, after))

        return transitions

    def test_detects_consistent_region(self, detector, synthetic_menu_transitions):
        """Test that detector finds the menu region."""
        regions = detector.detect_state_regions(
            synthetic_menu_transitions,
            consistency_threshold=0.6,
            min_region_area=1000
        )

        assert len(regions) >= 1, "Should detect at least one region"

        # Check if detected region overlaps with actual menu (100, 100, 200, 300)
        menu_bbox = (100, 100, 200, 300)
        found_menu = False

        for region in regions:
            if self._bboxes_overlap(region.bbox, menu_bbox, min_iou=0.5):
                found_menu = True
                break

        assert found_menu, "Should detect the menu region"

    def test_requires_minimum_examples(self, detector):
        """Test that detector requires enough examples."""
        # Only 5 examples
        transitions = [
            (
                np.random.randint(0, 255, (100, 100), dtype=np.uint8),
                np.random.randint(0, 255, (100, 100), dtype=np.uint8)
            )
            for _ in range(5)
        ]

        with pytest.raises(ValueError, match="at least 10"):
            detector.detect_state_regions(transitions)

    def test_consistency_scores(self, detector, synthetic_menu_transitions):
        """Test that consistency scores are reasonable."""
        regions = detector.detect_state_regions(synthetic_menu_transitions)

        for region in regions:
            assert 0.0 <= region.consistency_score <= 1.0, \
                "Consistency score should be in [0, 1]"

    def _bboxes_overlap(self, bbox1, bbox2, min_iou=0.5):
        """Check if two bounding boxes overlap sufficiently."""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2

        # Compute intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)

        if x_right < x_left or y_bottom < y_top:
            return False

        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = w1 * h1 + w2 * h2 - intersection

        iou = intersection / union if union > 0 else 0
        return iou >= min_iou
```

#### 7.2: Integration Tests

**`qontinui/tests/integration/test_state_building.py`**

```python
"""Integration tests for complete state building pipeline."""

import pytest
import numpy as np
from pathlib import Path

from qontinui.discovery.state_construction.state_builder import (
    StateBuilder,
    TransitionInfo
)


class TestStateBuilding:
    """Test complete state building from screenshots to State objects."""

    @pytest.fixture
    def state_builder(self):
        return StateBuilder()

    @pytest.fixture
    def sample_screenshots(self):
        """Load sample screenshots from test data."""
        # TODO: Add real screenshot test data
        return [
            np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
            for _ in range(10)
        ]

    def test_builds_complete_state(self, state_builder, sample_screenshots):
        """Test that state builder creates complete State object."""
        state = state_builder.build_state_from_screenshots(
            screenshot_sequence=sample_screenshots
        )

        assert state is not None
        assert state.name != ''
        assert isinstance(state.state_images, list)
        assert isinstance(state.state_regions, list)
        assert isinstance(state.state_locations, list)

    def test_state_name_generation(self, state_builder):
        """Test that meaningful names are generated."""
        # TODO: Create screenshot with clear title text
        pass

    def test_state_images_identified(self, state_builder, sample_screenshots):
        """Test that StateImages are identified from consistent elements."""
        # Need at least 2 screenshots to find consistency
        state = state_builder.build_state_from_screenshots(sample_screenshots)

        # Should find some consistent elements
        # (Exact count depends on test data)
        assert isinstance(state.state_images, list)
```

#### 7.3: End-to-End Tests

**`tests/e2e/test_runner_state_detection.py`**

```python
"""
End-to-end test for state detection in runner.

Tests the complete flow:
1. Capture screenshots in runner
2. Process locally with qontinui library
3. Generate state structure
4. Upload to web
"""

import pytest
import tempfile
from pathlib import Path
import json

# This would test the actual runner integration
# Skipping implementation for brevity
```

---

### Phase 8: Documentation & Rollout (Week 8)

#### 8.1: Documentation

**`qontinui/docs/STATE_DETECTION.md`**

```markdown
# State Detection in qontinui

## Overview

State detection automatically identifies distinct application states from
screenshot sequences and user input. This enables automatic generation of
state structures for model-based GUI automation.

## How It Works

### 1. Differential Consistency Detection

Identifies state boundaries by finding pixels that change consistently
together across multiple transitions to the same state.

**Example:** When opening a menu 1000 times:
- Menu pixels: Always change from background → menu (high consistency)
- Background pixels: Random animation changes (low consistency)
- Result: Menu region is clearly identified

**Usage:**

```python
from qontinui.discovery.state_detection import DifferentialConsistencyDetector

detector = DifferentialConsistencyDetector()

# Provide before/after screenshot pairs
transitions = [
    (before_img1, after_img1),
    (before_img2, after_img2),
    # ... 100-1000 pairs
]

regions = detector.detect_state_regions(
    transitions,
    consistency_threshold=0.7,
    min_region_area=500
)

for region in regions:
    print(f"Found region at {region.bbox} with score {region.consistency_score}")
```

### 2. State Construction

Builds complete State objects with meaningful names and components.

**Usage:**

```python
from qontinui.discovery.state_construction import StateBuilder

builder = StateBuilder()

state = builder.build_state_from_screenshots(
    screenshot_sequence=screenshots,  # Screenshots where state is active
    transitions_to_state=transitions  # How we got to this state
)

print(f"State name: {state.name}")
print(f"StateImages: {len(state.state_images)}")
print(f"StateRegions: {len(state.state_regions)}")
print(f"StateLocations: {len(state.state_locations)}")
```

### 3. OCR-Based Naming

Automatically generates meaningful names using text extraction.

**Examples:**
- Window title bar "Inventory - Player 1" → `inventory_player_1`
- Button with text "Continue" → `continue_button`
- Generic element → `button_120_450` (position-based)

## Local vs. Cloud Processing

### Local (Recommended for Development & Production)

**Benefits:**
- No AWS costs
- Full privacy (data stays local)
- Fast (no network transfer)
- Works offline

**Usage in qontinui-runner:**

```typescript
import { StateDetectionService } from './services/StateDetectionService';

const service = new StateDetectionService();

const result = await service.processSession(
  './captures/screenshots',
  './captures/input-events.json',
  './output/states.json'
);

console.log(`Detected ${result.totalStates} states`);
```

### Cloud (Optional Premium Feature)

**Benefits:**
- SAM3 refinement (premium)
- Team collaboration
- Centralized storage

**Usage via API:**

```typescript
await fetch('/api/v1/state-detection/analyze-transitions', {
  method: 'POST',
  body: formData  // Screenshots + metadata
});
```

## Best Practices

### Data Collection

**Minimum Requirements:**
- 10+ transitions to each state (more is better)
- 100-1000+ transitions = excellent results
- Consistent before/after pairs

**Tips:**
- Record multiple attempts at same transition
- Include variations (different starting positions)
- Capture full GUI context (don't crop)

### Parameter Tuning

**consistency_threshold** (0-1):
- Higher = more strict (only very consistent regions)
- Lower = more permissive (may include noise)
- Recommended: 0.6-0.8

**min_region_area** (pixels):
- Filter out tiny noise regions
- Recommended: 500-1000 for desktop apps

### Performance

**Processing Time (Local i5):**
- 100 screenshots: ~10 seconds
- 1000 screenshots: ~60 seconds
- 10,000 screenshots: ~10 minutes

**Memory Usage:**
- ~2MB per screenshot
- 1000 screenshots = ~2GB RAM

## Examples

See `examples/state_detection_demo.py` for complete working example.
```

#### 8.2: Migration Guide

**`MIGRATION_GUIDE.md`**

```markdown
# Migration Guide: Detection Code Consolidation

## For qontinui-web Developers

### Old Import Pattern

```python
# OLD (deprecated)
from app.services.analysis.analyzers.button_detector import ButtonDetector
```

### New Import Pattern

```python
# NEW
from qontinui.discovery.element_detection.button_detector import ButtonDetector
```

### Deprecation Timeline

- **Week 1-2:** Old imports still work (with warnings)
- **Week 3-4:** Old imports raise deprecation errors
- **Week 5+:** Old code removed

### Migration Script

Run the automated migration script:

```bash
python scripts/update_imports.py --check  # Dry run
python scripts/update_imports.py --fix    # Apply changes
```

## For API Users

### API Changes

Most endpoints remain the same, but now delegate to qontinui library.

**No breaking changes** - existing API calls continue to work.

### New Endpoints

```
POST /api/v1/state-detection/analyze-transitions
POST /api/v1/state-detection/detect-regions
GET  /api/v1/state-detection/states
```

## For Runner Developers

### New Functionality

State detection is now available locally:

```typescript
import { StateDetectionService } from './services/StateDetectionService';

const service = new StateDetectionService();
const result = await service.processSession(...);
```

See `docs/RUNNER_INTEGRATION.md` for details.
```

---

## Rollout Plan

### Week 1-2: Foundation
- ✅ Create directory structure
- ✅ Set up base classes
- ✅ Migration utilities
- ✅ Testing infrastructure

### Week 2-3: Algorithm Migration
- ✅ Move element detectors (day 1-2)
- ✅ Move region analyzers (day 3-4)
- ✅ Move experimental (day 5)
- ✅ Update imports (day 6-7)
- ✅ Deprecation warnings (day 7)

### Week 3-5: New Features
- ✅ Differential Consistency Detector (week 3)
- ✅ StateBuilder (week 4)
- ✅ OCR Name Generator (week 4)
- ✅ Element Identifier (week 5)
- ✅ Integration & testing (week 5)

### Week 5: API Updates
- ✅ Update qontinui-api endpoints
- ✅ Add new state detection endpoints
- ✅ Update documentation
- ✅ API testing

### Week 5-6: Runner Integration
- ✅ Python bridge service (week 5)
- ✅ TypeScript integration (week 6)
- ✅ CLI tools (week 6)
- ✅ Testing (week 6)

### Week 6-7: Frontend
- ✅ Runner UI components (week 6)
- ✅ Web UI components (week 7)
- ✅ Visualization tools (week 7)
- ✅ User testing (week 7)

### Week 7-8: Testing & Launch
- ✅ Unit tests (week 7)
- ✅ Integration tests (week 7)
- ✅ E2E tests (week 8)
- ✅ Documentation (week 8)
- ✅ Beta release (week 8)

---

## Risk Mitigation

### Technical Risks

**Risk:** Breaking existing functionality during migration
**Mitigation:**
- Maintain backward compatibility during transition
- Comprehensive test coverage
- Gradual rollout with deprecation warnings

**Risk:** Performance degradation
**Mitigation:**
- Benchmark before/after migration
- Optimize hot paths
- Profile local processing

**Risk:** Import conflicts between old and new code
**Mitigation:**
- Clear deprecation timeline
- Automated migration script
- CI checks for old imports

### Business Risks

**Risk:** User confusion during transition
**Mitigation:**
- Clear documentation
- Migration guide
- Support channels ready

**Risk:** Disruption to development workflow
**Mitigation:**
- Coordinate with team
- Staged rollout
- Rollback plan ready

---

## Success Metrics

### Technical Metrics

- ✅ 100% of detection code migrated to library
- ✅ Zero breaking API changes
- ✅ <10% performance regression (ideally improvement)
- ✅ 90%+ test coverage on new features
- ✅ Local processing works on target hardware (i5 MacBook)

### Business Metrics

- ✅ 1000 screenshots processable locally in <2 minutes
- ✅ AWS costs < $1/month per user for basic tier
- ✅ State detection accuracy >80% (human validation)
- ✅ User satisfaction with local processing
- ✅ Successful beta with 10+ users

---

## Next Steps

1. **Review & Approve:** Get team sign-off on plan
2. **Set Up Project:** Create tracking board with all tasks
3. **Kick Off Week 1:** Start with foundation phase
4. **Weekly Reviews:** Check progress, adjust timeline
5. **Beta Launch:** Deploy to test users in week 8

**Estimated Total Effort:** 6-8 weeks (1-2 developers full-time)

---

## Appendix: File Checklist

### Files to Create (40+ new files)

**qontinui library:**
- [ ] `discovery/element_detection/` (15 detector files)
- [ ] `discovery/region_analysis/` (12 analyzer files)
- [ ] `discovery/state_detection/` (4 files including new differential detector)
- [ ] `discovery/state_construction/` (5 new files)
- [ ] `discovery/experimental/` (5 files)
- [ ] `api/state_detection_api.py`

**qontinui-api:**
- [ ] Update `state_discovery_api.py`
- [ ] New endpoints in router

**qontinui-runner:**
- [ ] `python-bridge/services/state_detection_service.py`
- [ ] `src/services/StateDetectionService.ts`
- [ ] `src/components/StateViewer.tsx`

**qontinui-web:**
- [ ] `frontend/src/components/state-detection-viewer.tsx`
- [ ] Backend import updates (40+ files)

**Tests:**
- [ ] Unit tests (20+ files)
- [ ] Integration tests (5+ files)
- [ ] E2E tests (3+ files)

**Documentation:**
- [ ] `STATE_DETECTION.md`
- [ ] `MIGRATION_GUIDE.md`
- [ ] `RUNNER_INTEGRATION.md`
- [ ] API documentation updates

---

**Total:** ~100 files to create/modify
