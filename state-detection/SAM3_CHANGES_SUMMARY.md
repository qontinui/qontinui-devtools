# SAM3 Integration - Changes Summary

This document summarizes all changes made to integrate SAM3 (Segment Anything Model 3) with text-prompted segmentation into the qontinui-web application.

## Overview

- **Date:** 2025-11-24
- **Status:** ✅ Implementation Complete (pending testing)
- **Agents Used:** 2 parallel agents (backend + frontend)

---

## Backend Changes

### 1. Fixed HAS_SAM2 → HAS_SAM3 Bug

**File:** `qontinui/src/qontinui/semantic/processors/sam3_processor.py`

**Line 337:**
```python
# BEFORE:
if not HAS_SAM2 or self.predictor is None:

# AFTER:
if not HAS_SAM3 or self.processor is None:
```

**Impact:** Fixed a critical bug that would cause runtime errors in the `process_with_prompts()` method.

---

### 2. Added SAM3 Imports and Availability Checks

**File:** `qontinui-api/semantic_api.py`

**Lines 31-39:**
```python
try:
    from qontinui.semantic.processors.sam3_processor import SAM3Processor, HAS_SAM3
    SAM3_AVAILABLE = HAS_SAM3
except ImportError:
    SAM3_AVAILABLE = False
    HAS_SAM3 = False
    logging.warning("SAM3Processor not available - using fallback implementation")
```

**Impact:** Graceful fallback if SAM3 is not installed, with clear logging.

---

### 3. Initialize SAM3Processor at API Startup

**File:** `qontinui-api/semantic_api.py`

**Lines 742-758:**
```python
sam3_processor = None
if SAM3_AVAILABLE:
    try:
        sam3_processor = SAM3Processor()
        logger.info("SAM3Processor initialized successfully")
    except FileNotFoundError as e:
        logger.warning(f"SAM3 model checkpoint not found: {e}")
        logger.info("To enable SAM3, ensure the model checkpoint is available")
        SAM3_AVAILABLE = False
    except ImportError as e:
        logger.warning(f"SAM3 dependencies not installed: {e}")
        logger.info("To enable SAM3, install required dependencies: pip install sam3")
        SAM3_AVAILABLE = False
    except Exception as e:
        logger.warning(f"Failed to initialize SAM3Processor: {e}")
        logger.info("SAM3 will not be available, falling back to OpenCV implementation")
        SAM3_AVAILABLE = False
```

**Impact:**
- Processor initialized once at startup (not per request)
- Comprehensive error handling with helpful messages
- Automatic fallback to OpenCV if initialization fails

---

### 4. Added Conversion Helper Function

**File:** `qontinui-api/semantic_api.py`

**Lines 761-804:**
```python
def _convert_qontinui_scene_to_api_objects(
    scene: Any, processor: RealSemanticProcessor
) -> list[SemanticObject]:
    """Convert qontinui SemanticScene objects to API SemanticObject format."""
    # ... implementation ...
```

**Impact:** Converts between qontinui's internal format and API response format with robust mask encoding.

---

### 5. Replaced OpenCV Implementation with Real SAM3

**File:** `qontinui-api/semantic_api.py`

**Lines 821-848 (process_screenshot endpoint):**

**BEFORE:**
```python
if request.strategy == "sam3" and request.text_prompt:
    objects = processor._segment_with_masks(image, request.options, text_prompt=request.text_prompt)
else:
    objects = processor.detect_ui_elements(image, request.options, request.strategy)
```

**AFTER:**
```python
if request.strategy == "sam3":
    if not SAM3_AVAILABLE or sam3_processor is None:
        raise HTTPException(
            status_code=503,
            detail="SAM3 is not available. Model checkpoint may not be downloaded. "
            "See installation instructions.",
        )

    try:
        # Use the real SAM3Processor with text prompt
        scene = sam3_processor.process(image, text_prompt=request.text_prompt)
        objects = _convert_qontinui_scene_to_api_objects(scene, processor)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"SAM3 model checkpoint not found: {str(e)}. "
            "Please download the checkpoint first.",
        )
    except Exception as e:
        logger.error(f"SAM3 processing failed: {e}, falling back to OpenCV")
        objects = processor._segment_with_masks(
            image, request.options, text_prompt=request.text_prompt
        )
else:
    objects = processor.detect_ui_elements(image, request.options, request.strategy)
```

**Impact:**
- Now uses actual SAM3Processor with neural network
- Passes text_prompt to enable concept-based segmentation
- Returns HTTP 503 if SAM3 not available (instead of silently falling back)
- Falls back to OpenCV only if processing fails

---

### 6. Updated Health Check Endpoint

**File:** `qontinui-api/semantic_api.py`

**Lines 942-952:**
```python
@router.get("/semantic/health")
async def health_check():
    """Check API health and model availability."""
    return {
        "status": "healthy",
        "qontinui_available": QONTINUI_AVAILABLE,
        "clip_available": CLIP_AVAILABLE,
        "sam3_available": SAM3_AVAILABLE,  # ← NEW
    }
```

**Impact:** Now reports SAM3 availability for diagnostics.

---

## Frontend Changes

### File: `qontinui-web/frontend/src/components/SemanticAnalysis/SemanticAnalysisTab.tsx`

### 1. Added Import (Line 9)
```typescript
import { Input } from "@/components/ui/input"
```

### 2. Added State Variables (Line 50)
```typescript
const [textPrompt, setTextPrompt] = useState('')
const [strategy, setStrategy] = useState<'sam2' | 'sam3' | 'ocr' | 'hybrid'>('hybrid')
```

### 3. Updated API Request (Lines 99-116)
```typescript
const requestBody: any = {
  image: selectedImage,
  strategy,
  options,
}

// Only include text_prompt if it's not empty and strategy is sam3
if (textPrompt.trim() && strategy === 'sam3') {
  requestBody.text_prompt = textPrompt.trim()
}

const response = await fetch(`${API_BASE_URL}/api/semantic/process`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestBody),
})
```

### 4. Added SAM3 Strategy Button (Lines 397-405)
```typescript
<Button
  variant={strategy === 'sam3' ? 'default' : 'outline'}
  className="h-auto p-3 flex flex-col items-center gap-2"
  onClick={() => setStrategy('sam3')}
  title="Segment Anything Model v3 - text-prompted segmentation"
>
  <Sparkles className="h-5 w-5" />
  <span className="text-sm">SAM3</span>
</Button>
```

### 5. Added Text Prompt Controls (Lines 436-469)

**Text Input:**
```typescript
<Input
  type="text"
  value={textPrompt}
  onChange={(e) => setTextPrompt(e.target.value)}
  placeholder="e.g., button, icon, text field..."
  className="bg-gray-800/50 border-gray-700 text-white placeholder:text-gray-500"
/>
```

**Preset Buttons:**
```typescript
<div className="flex flex-wrap gap-2">
  {['Everything', 'Button', 'Icon', 'Text Field', 'Checkbox', 'Link', 'Menu Item'].map(
    (preset) => (
      <Button
        key={preset}
        size="sm"
        variant={textPrompt === preset.toLowerCase() ? 'default' : 'outline'}
        onClick={() => setTextPrompt(preset.toLowerCase())}
        className="h-6 text-xs"
      >
        {preset}
      </Button>
    )
  )}
</div>
```

**Impact:**
- Users can now enter custom text prompts
- Quick preset buttons for common UI elements
- Controls only visible when SAM3 strategy is selected
- Follows existing UI patterns and dark theme

---

## New Files Created

### 1. INSTALL_SAM3.md
- Complete installation guide
- Prerequisites and dependencies
- Step-by-step authentication
- Troubleshooting section
- Performance expectations

### 2. SAM3_CHANGES_SUMMARY.md (this file)
- Comprehensive changelog
- Before/after code comparisons
- Impact analysis

---

## Testing Checklist

### Before Testing
- [ ] Request Hugging Face access to facebook/sam3
- [ ] Install dependencies: `pip install torch==2.7.0 huggingface_hub`
- [ ] Install SAM3: `pip install git+https://github.com/facebookresearch/sam3.git`
- [ ] Authenticate: `huggingface-cli login`

### Backend Tests
- [ ] Start API: `uvicorn semantic_api:app --reload`
- [ ] Check health: `curl http://localhost:8000/api/semantic/health`
- [ ] Verify `sam3_available: true` in health response
- [ ] Check logs for "SAM3Processor initialized successfully"

### Frontend Tests
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Upload a GUI screenshot
- [ ] Select "SAM3" strategy
- [ ] Verify text prompt controls appear
- [ ] Test custom prompt: Enter "button"
- [ ] Test preset button: Click "Icon"
- [ ] Click "Process Image"
- [ ] Verify segmentation results with colored masks

### Error Handling Tests
- [ ] Test without SAM3 installed (should show error message)
- [ ] Test with invalid text prompt (should handle gracefully)
- [ ] Test with empty prompt (should process everything)
- [ ] Check fallback to OpenCV if SAM3 fails

---

## Performance Expectations

| Scenario | Expected Behavior |
|----------|-------------------|
| **SAM3 Available + Text Prompt** | Real SAM3 with concept-based segmentation |
| **SAM3 Available + No Prompt** | Real SAM3 with automatic grid segmentation |
| **SAM3 Not Available** | HTTP 503 error with installation instructions |
| **SAM3 Processing Fails** | Logs error, falls back to OpenCV |

---

## Architecture Flow

```
User uploads image
    ↓
Frontend (SemanticAnalysisTab.tsx)
    ↓ [Selects SAM3 strategy + enters text prompt]
POST /api/semantic/process
    ↓
semantic_api.py (process_screenshot)
    ↓ [Checks SAM3_AVAILABLE]
sam3_processor.process(image, text_prompt="button")
    ↓ [Real SAM3 neural network inference]
Returns SemanticScene with masks
    ↓ [Convert to API format]
Frontend displays colored masks + bounding boxes
```

---

## Known Limitations

1. **GPU Required:** SAM3 is very slow on CPU (30-60s per image)
2. **Model Size:** 3.5 GB checkpoint download required
3. **Access Required:** Must request Hugging Face access
4. **Memory:** Requires 8+ GB GPU memory for good performance

---

## Next Steps

1. Complete installation following `INSTALL_SAM3.md`
2. Run backend and frontend tests
3. Test with real GUI screenshots
4. Monitor performance and adjust as needed
5. Consider AWS deployment for production (see previous discussion)

---

## Related Documentation

- Installation Guide: `/Users/jspinak/Documents/qontinui/INSTALL_SAM3.md`
- SAM3 Official Repo: https://github.com/facebookresearch/sam3
- Hugging Face Model: https://huggingface.co/facebook/sam3
- Meta Blog Post: https://ai.meta.com/blog/segment-anything-model-3/
