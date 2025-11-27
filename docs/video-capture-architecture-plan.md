# Video-Based Capture Architecture Plan

## Overview

This document describes the new architecture for capturing, processing, and streaming GUI automation data. The key changes are:

1. **Replace screenshot capture with continuous video recording**
2. **Capture ALL input events** (mouse clicks, drags, scrolls, keyboard)
3. **Process data locally** on user's machine
4. **Stream compressed data** to cloud (AWS)
5. **Support full-size screenshot import** for state structure development
6. **Export only configuration files** (StateImages, not raw screenshots)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER'S LOCAL MACHINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LOCAL CAPTURE LAYER                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │   │
│  │  │Video Recorder│    │Input Monitor │    │  Timestamp   │          │   │
│  │  │   (FFmpeg)   │    │  (pynput)    │    │  Correlator  │          │   │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │   │
│  │         │                   │                   │                   │   │
│  │         ▼                   ▼                   ▼                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              LOCAL STORAGE (Full Quality)                    │   │   │
│  │  │  ├── videos/session_{id}.mp4 (H.264, 30fps)                 │   │   │
│  │  │  ├── events/session_{id}.jsonl (input events + timestamps)  │   │   │
│  │  │  └── frames/ (extracted on-demand)                          │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   LOCAL PROCESSING LAYER                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │   │
│  │  │Frame Extractor│   │State Detector│    │ Region/Image │          │   │
│  │  │(on-demand)   │    │   (ML/CV)    │    │  Extractor   │          │   │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │   │
│  │         │                   │                   │                   │   │
│  │         ▼                   ▼                   ▼                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              PROCESSED DATA                                  │   │   │
│  │  │  ├── states/ (detected state definitions)                   │   │   │
│  │  │  ├── elements/ (StateImages, regions, locations)            │   │   │
│  │  │  └── processing_log.json (for review/refinement)            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket (compressed)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐                        │
│  │   qontinui-web      │    │   qontinui-train    │                        │
│  │   (Backend API)     │    │   (Training Data)   │                        │
│  └──────────┬──────────┘    └──────────┬──────────┘                        │
│             │                          │                                    │
│             ▼                          ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         S3 STORAGE                                   │   │
│  │  ├── compressed-videos/ (low-res for preview)                       │   │
│  │  ├── thumbnails/ (frame thumbnails)                                 │   │
│  │  ├── events/ (input event logs)                                     │   │
│  │  ├── processed/ (states, elements from local processing)            │   │
│  │  ├── full-screenshots/ (on-demand, requested by user)               │   │
│  │  └── automation-runs/ (integration test data)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow by Use Case

### 1. Manual Capture Session (Building State Structure)

```
USER ACTION                    LOCAL                           CLOUD
───────────────────────────────────────────────────────────────────────────

Start Capture ──────────────► Start FFmpeg recording
                              Start input monitoring

User interacts ─────────────► Record video (30fps)
with target app               Log all inputs with timestamps:
                              - Mouse: click, drag, scroll, move
                              - Keyboard: keypress, keyrelease

Stop Capture ───────────────► Stop recording
                              Finalize event log

                              ─────────────────────────────► Stream:
                                                             - Compressed video
                                                             - Event log
                                                             - Thumbnails

Request Processing ─────────► Extract frames at input events
                              Run state detection (ML/CV)
                              Extract regions/images
                              Generate processing log

                              ─────────────────────────────► Stream:
                                                             - Detected states
                                                             - State elements
                                                             - Processing log
                                                             - Source screenshots
                                                               (full-size, for editing)
```

### 2. Running Automation (Integration Testing)

```
USER ACTION                    LOCAL                           CLOUD
───────────────────────────────────────────────────────────────────────────

Load Config ────────────────► Load state structure

Start Automation ───────────► Start video recording
                              Execute automation steps
                              Log actions + results

                              ─────────────────────────────► Real-time stream:
                                                             - Compressed video
                                                             - Action events
                                                             - State transitions
                                                             - Match results

Stop Automation ────────────► Stop recording
                              Finalize run data

                              ─────────────────────────────► Stream:
                                                             - Run summary
                                                             - Test results
                                                             - Failure screenshots
```

---

## Component Specifications

### 1. Video Capture Service

**Location:** `python-bridge/services/video_capture_service.py`

```python
@dataclass
class VideoCaptureConfig:
    fps: int = 30                    # Frame rate
    codec: str = "h264"              # H.264 for compatibility
    quality: str = "high"            # CRF 18 for local, 28 for cloud
    resolution: str = "native"       # Capture at screen resolution
    audio: bool = False              # No audio needed

@dataclass
class CompressedStreamConfig:
    fps: int = 10                    # Lower for streaming
    resolution: Tuple[int, int] = (1280, 720)  # 720p max
    bitrate: str = "1M"              # 1 Mbps
```

**Capabilities:**
- Dual output: full quality local + compressed stream
- Platform-specific capture (gdigrab/avfoundation/x11grab)
- Frame timestamp metadata for correlation

### 2. Input Monitor Service

**Location:** `python-bridge/services/input_monitor_service.py`

```python
@dataclass
class InputEvent:
    timestamp: float          # Unix timestamp (ms precision)
    frame_number: int         # Calculated: (timestamp - start) * fps
    event_type: str           # "mouse_click", "mouse_drag", "key_press", etc.

    # Mouse events
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None      # "left", "right", "middle"
    scroll_delta: Optional[int] = None
    drag_start: Optional[Tuple[int, int]] = None
    drag_end: Optional[Tuple[int, int]] = None

    # Keyboard events
    key: Optional[str] = None
    key_code: Optional[int] = None
    modifiers: List[str] = field(default_factory=list)  # ["ctrl", "shift", etc.]
```

**Events Captured:**

| Event Type | Trigger | Data |
|------------|---------|------|
| `mouse_click` | Button press + release | x, y, button, duration |
| `mouse_drag` | Button held + movement | start, end, path, button |
| `mouse_scroll` | Scroll wheel | x, y, delta |
| `mouse_move` | Cursor movement (sampled) | x, y (every 100ms or on stop) |
| `key_press` | Key down | key, code, modifiers |
| `key_release` | Key up | key, code, duration |
| `key_combo` | Multiple keys | keys[], modifiers |

### 3. Frame Extractor Service

**Location:** `python-bridge/services/frame_extractor_service.py`

```python
class FrameExtractor:
    def extract_at_timestamp(self, video_path: str, timestamp: float) -> PIL.Image:
        """Extract single frame at exact timestamp."""

    def extract_at_events(self, video_path: str, events: List[InputEvent],
                          filter: EventFilter) -> List[ExtractedFrame]:
        """Extract frames at filtered input events."""

    def extract_batch(self, video_path: str, timestamps: List[float]) -> List[ExtractedFrame]:
        """Batch extract for efficiency."""

@dataclass
class EventFilter:
    event_types: List[str] = field(default_factory=lambda: ["mouse_click"])
    buttons: List[str] = field(default_factory=lambda: ["left"])
    include_after_delay_ms: Optional[int] = None  # e.g., 1000ms after each event
    max_count: Optional[int] = None               # e.g., first 20

@dataclass
class ExtractedFrame:
    timestamp: float
    frame_number: int
    image: PIL.Image
    source_event: InputEvent
    path: Optional[str] = None  # If saved to disk
```

### 4. Cloud Streaming Service

**Location:** `python-bridge/services/cloud_streaming_service.py`

**Streamed Data (Compressed):**

| Data Type | Format | Size Estimate |
|-----------|--------|---------------|
| Video | H.264, 720p, 10fps, 1Mbps | ~7.5 MB/min |
| Thumbnails | JPEG, 320x180 | ~10 KB each |
| Events | JSONL, gzipped | ~1 KB/100 events |
| Processed states | JSON + PNG thumbnails | ~50 KB/state |

**Full-Size Data (On Request):**

| Data Type | When Sent | Format |
|-----------|-----------|--------|
| Screenshots | User requests via filter | PNG, native resolution |
| State source images | After processing, for editing | PNG, native resolution |

### 5. Local Processing Pipeline

**Location:** `python-bridge/services/local_processor.py`

```python
class LocalProcessor:
    def process_capture_session(self, session_id: str, config: ProcessingConfig) -> ProcessingResult:
        """
        1. Extract frames at input events
        2. Detect unique states (screen clustering)
        3. Identify state elements (buttons, fields, etc.)
        4. Extract StateImages with positions
        5. Generate processing log for review
        """

@dataclass
class ProcessingConfig:
    # State detection
    state_similarity_threshold: float = 0.95
    min_state_duration_ms: int = 500

    # Element detection
    detect_buttons: bool = True
    detect_text_fields: bool = True
    detect_images: bool = True

    # StateImage extraction
    extract_fixed_positions: bool = True
    position_tolerance_px: int = 5

@dataclass
class ProcessingResult:
    states: List[DetectedState]
    elements: List[StateElement]
    processing_log: ProcessingLog  # For review/refinement
    source_screenshots: List[str]  # Paths to full-size images used
```

---

## Analysis Methods & Algorithms

This section describes the analysis methods used for automatic state structure generation from captured video and input events.

### Analysis Pipeline Overview

```
Video + Events → State Boundary Detection → Image Extraction → Element Detection → Transition Analysis
                         ↓                        ↓                    ↓                   ↓
                 Unique screen states    StateImages within    Clickable elements   State transitions
                 identified via          state boundaries      buttons, fields      with actions
                 visual clustering       are extracted         icons detected
```

### 1. State Boundary Detection

**Purpose:** Identify when the screen represents different "states" (unique screens/views).

**Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **SSIM Clustering** | Structural Similarity Index to cluster visually similar frames | General state detection |
| **Perceptual Hashing** | pHash/dHash for fast frame grouping | Large video sets, initial pass |
| **Feature Clustering** | SIFT/ORB features + DBSCAN clustering | Robust to minor variations |
| **Optical Flow Analysis** | Detect major visual changes between frames | Detecting transition moments |
| **Histogram Comparison** | Color/intensity histogram differences | Fast coarse detection |

**Implementation:**
```python
@dataclass
class StateBoundaryConfig:
    # Clustering parameters
    similarity_threshold: float = 0.92  # SSIM threshold for "same state"
    clustering_algorithm: str = "dbscan"  # "dbscan", "hierarchical", "kmeans"
    min_state_duration_ms: int = 500     # Ignore transient states

    # Feature extraction
    feature_extractor: str = "orb"  # "sift", "orb", "surf"
    feature_count: int = 500

    # Transition detection
    optical_flow_threshold: float = 0.3  # Movement magnitude for transition

class StateBoundaryDetector:
    def detect_states(self, frames: List[Frame]) -> List[DetectedState]:
        """
        1. Extract features from each frame
        2. Compute pairwise similarity matrix
        3. Cluster frames into states
        4. Identify state transition points
        5. Return unique states with representative frames
        """

    def identify_transitions(self, frames: List[Frame], events: List[InputEvent]) -> List[TransitionPoint]:
        """
        Correlate visual changes with input events to identify
        where transitions occur.
        """
```

### 2. Image Extraction (StateImages)

**Purpose:** Extract identifying images that belong to detected states.

**Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **Template Matching** | OpenCV matchTemplate for known patterns | Fixed UI elements |
| **Edge Detection** | Canny/Sobel to find UI element boundaries | Clean UI designs |
| **Contour Analysis** | findContours to isolate distinct regions | Button/icon extraction |
| **Connected Components** | Label connected regions as candidates | Text/icon isolation |
| **Saliency Detection** | Identify visually prominent regions | Important UI elements |

**State-Bounded Extraction:**

Images are extracted *within the boundaries of their parent states*. This ensures:
- Images are associated with correct states
- Position information is relative to state boundaries
- Fixed-position elements are correctly identified

```python
@dataclass
class ImageExtractionConfig:
    min_size: Tuple[int, int] = (20, 20)
    max_size: Tuple[int, int] = (500, 500)
    edge_detection: str = "canny"
    contour_approximation: float = 0.02
    extract_at_click_locations: bool = True
    click_region_padding: int = 20

class StateImageExtractor:
    def extract_from_state(self, state: DetectedState, frames: List[Frame],
                           events: List[InputEvent]) -> List[ExtractedImage]:
        """
        1. Get frames belonging to this state
        2. Identify click locations within state
        3. Extract regions around click locations
        4. Detect additional UI elements via contour analysis
        5. Assign positions (fixed vs. dynamic)
        """

    def determine_position_type(self, image: ExtractedImage,
                                 occurrences: List[Occurrence]) -> PositionType:
        """
        Analyze multiple occurrences to determine if position is fixed
        (same location across frames) or dynamic.
        """
```

### 3. Element Detection (UI Components)

**Purpose:** Identify and classify UI elements (buttons, text fields, icons, etc.).

**Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **YOLO/Faster R-CNN** | Object detection for UI elements | Pre-trained on UI datasets |
| **OCR + Heuristics** | Text detection for labels/buttons | Text-based UI |
| **Shape Recognition** | Detect rectangles, circles, icons | Standard UI patterns |
| **Semantic Segmentation** | Pixel-level UI element classification | Complex interfaces |
| **Visual Grounding** | Vision-language models for element finding | Dynamic/unusual UIs |

```python
@dataclass
class ElementDetectionConfig:
    detector_model: str = "yolo_ui"  # Pre-trained UI element detector
    confidence_threshold: float = 0.7
    detect_types: List[str] = field(default_factory=lambda: [
        "button", "text_field", "checkbox", "dropdown",
        "icon", "link", "tab", "menu_item"
    ])
    use_ocr: bool = True
    ocr_engine: str = "tesseract"

class ElementDetector:
    def detect_elements(self, frame: Frame) -> List[UIElement]:
        """
        Run object detection model to identify UI elements
        and their bounding boxes.
        """

    def classify_clicked_element(self, click_location: Point,
                                  elements: List[UIElement]) -> Optional[UIElement]:
        """
        Determine which detected element was clicked.
        """
```

### 4. Transition Analysis

**Purpose:** Identify and model state transitions from captured video and input events.

**Transition Model:**

A transition has two parts:
- **Outgoing (Action):** The GUI action that triggers the transition (e.g., click on StateImage)
- **Incoming (Recognition):** The appearance of StateImages in the destination state

```
┌─────────────────┐                      ┌─────────────────┐
│   State A       │    TRANSITION        │   State B       │
│                 │                      │                 │
│  ┌───────────┐  │   Outgoing:          │  ┌───────────┐  │
│  │ login_btn │──┼─► Click on           │  │ welcome   │  │
│  └───────────┘  │   "login_btn"        │  │ _message  │  │
│                 │                      │  └───────────┘  │
│                 │   Incoming:          │                 │
│                 │   Recognition of  ◄──┼──"welcome_message"
│                 │   StateImage         │   appears       │
└─────────────────┘                      └─────────────────┘
```

**Transition Types:**

| Type | Description | Detection Method |
|------|-------------|------------------|
| **Click Transition** | State change after mouse click | Correlate click event with state change |
| **Key Transition** | State change after keyboard input | Correlate key event (e.g., Enter) with state change |
| **Auto Transition** | State change without user input | Detect state change with no recent input |
| **Multi-State** | Multiple states appear/disappear | Track all state changes in transition window |

```python
@dataclass
class Transition:
    id: str
    source_states: List[str]      # States active before transition
    target_states: List[str]       # States active after transition
    states_appeared: List[str]     # New states that appeared
    states_disappeared: List[str]  # States that were removed

    # Outgoing (Action)
    action_type: str              # "click", "key_press", "drag", etc.
    action_target: Optional[str]   # StateImage ID that was acted upon
    action_location: Optional[Point]
    action_data: dict             # Key pressed, button clicked, etc.

    # Incoming (Recognition)
    recognition_images: List[str]  # StateImages that identify target state
    recognition_confidence: float

    timestamp: float
    frame_before: int
    frame_after: int

class TransitionAnalyzer:
    def analyze_transitions(self, states: List[DetectedState],
                            events: List[InputEvent],
                            frames: List[Frame]) -> List[Transition]:
        """
        1. Identify state change points (states appearing/disappearing)
        2. Correlate with input events (find action that caused change)
        3. Identify outgoing action (click on which StateImage?)
        4. Identify incoming recognition (which StateImages appeared?)
        5. Build transition graph
        """

    def identify_action_target(self, event: InputEvent,
                                frame: Frame,
                                state: DetectedState) -> Optional[str]:
        """
        Determine which StateImage was clicked/acted upon.
        Returns StateImage ID if found.
        """

    def identify_recognition_images(self, state: DetectedState) -> List[str]:
        """
        Return StateImages that uniquely identify this state
        for transition recognition.
        """
```

**Automated Transition Creation:**

```python
class AutoTransitionBuilder:
    def build_from_capture(self, session: CaptureSession) -> List[Transition]:
        """
        Automatically create transitions from captured video:

        1. For each state change detected:
           a. Find the input event that preceded the change
           b. Extract the StateImage at the click/action location (outgoing)
           c. Identify StateImages that appeared in new state (incoming)
           d. Create Transition object

        2. Handle multi-state transitions:
           a. Track all states before/after
           b. Identify which states appeared/disappeared
           c. Create appropriate transition linking them
        """

    def suggest_transition_name(self, transition: Transition) -> str:
        """
        Generate human-readable name like:
        "Login Screen → Dashboard (click login_button)"
        """
```

### 5. Combined Analysis Pipeline

The analysis methods work together in a pipeline:

```python
class AnalysisPipeline:
    def __init__(self):
        self.state_detector = StateBoundaryDetector()
        self.image_extractor = StateImageExtractor()
        self.element_detector = ElementDetector()
        self.transition_analyzer = TransitionAnalyzer()

    def analyze_session(self, session: CaptureSession) -> AnalysisResult:
        # Phase 1: Detect state boundaries
        states = self.state_detector.detect_states(session.frames)

        # Phase 2: Extract images within state boundaries
        for state in states:
            state.images = self.image_extractor.extract_from_state(
                state, session.frames, session.events
            )

        # Phase 3: Detect UI elements
        for state in states:
            state.elements = self.element_detector.detect_elements(
                state.representative_frame
            )

        # Phase 4: Analyze transitions
        transitions = self.transition_analyzer.analyze_transitions(
            states, session.events, session.frames
        )

        return AnalysisResult(
            states=states,
            transitions=transitions,
            processing_log=self.get_processing_log()
        )
```

---

## Integration Testing of GUI Automation

This section describes how to test automation workflows using historical capture data as a simulated environment. This integrates with the existing **Verify / Integration Tests** page in qontinui-web.

### Key Distinction: Automation Testing vs. Software Testing

| Aspect | Software Testing (Process-Based) | Automation Testing (Model-Based) |
|--------|----------------------------------|----------------------------------|
| **What's tested** | External applications | The automation workflows themselves |
| **Test cases** | Discrete test cases created | No separate test cases - workflows ARE the tests |
| **Environment** | Real GUI of target application | Simulated environment using historical data |
| **Purpose** | Verify application behavior | Verify automation code correctness |

**This is integration testing of the automation code**, similar to integration testing any non-automation application. The difference is that GUI automation needs a simulated environment that can produce results of GUI actions - this is what the historical capture data provides.

### Simulated Environment Concept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL GUI AUTOMATION                                │
│                                                                             │
│   Automation Code  ──────►  Real GUI  ──────►  Actual Screen Changes        │
│                              (slow, flaky, requires running application)    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION TESTING WITH SIMULATED ENVIRONMENT            │
│                                                                             │
│   Automation Code  ──────►  Historical Data  ──────►  Simulated Results     │
│                              (fast, deterministic, no application needed)   │
│                                                                             │
│   "When states A,B are active and action X is performed,                    │
│    historical data shows states C,D become active"                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Historical data from automation runs** - Video + inputs from actual automation executions record what happens when actions are taken in specific state configurations

2. **Automation workflow executes against simulated environment** - Instead of clicking real buttons, the workflow's actions are matched against historical data

3. **Random selection from matches** - When multiple historical matches exist, one is chosen randomly. This makes each integration test run different, similar to live automation

4. **Workflow correctness is verified** - Does the automation code navigate correctly? Do transitions fire as expected?

5. **Immediate execution with optional visualization** - Tests run immediately by default, with options to visualize using screenshots or state element positions

### Core Components

```python
class GUISimulator:
    """
    Simulates GUI responses using historical capture data.
    Provides the 'environment' for testing automation workflows.
    """

    def __init__(self, historical_data: HistoricalData):
        self.history = historical_data
        self.current_states: Set[str] = set()

    def set_initial_states(self, states: Set[str]):
        """Set the starting state configuration."""
        self.current_states = states

    def execute_action(self, action: AutomationAction) -> SimulatedResult:
        """
        Simulate what would happen if this action were executed.
        Uses historical data to determine result.
        """
        # Find historical instances where this action was taken
        # from the same state configuration
        matching_history = self.history.find_matching(
            active_states=self.current_states,
            action_type=action.type,
            action_target=action.target
        )

        if not matching_history:
            return SimulatedResult(
                success=False,
                error="No historical data for this action from current states"
            )

        # RANDOM SELECTION: Choose randomly from matches
        # This makes each integration test run different, like live automation
        import random
        selected_match = random.choice(matching_history.matches)
        result_states = selected_match.active_states_after
        self.current_states = result_states

        return SimulatedResult(
            success=True,
            previous_states=self.current_states,
            resulting_states=result_states,
            selected_match=selected_match,  # Which historical instance was used
            total_matches=len(matching_history.matches)
        )

    def get_current_states(self) -> Set[str]:
        """Return currently active states in simulation."""
        return self.current_states


class AutomationWorkflowTester:
    """
    Tests automation workflows against simulated environment.
    No separate test cases needed - the workflow itself is the test.
    """

    def __init__(self, simulator: GUISimulator, workflow: AutomationWorkflow):
        self.simulator = simulator
        self.workflow = workflow

    def run_workflow(self) -> WorkflowTestResult:
        """
        Execute the automation workflow in simulated environment.
        Returns detailed results of each step.
        """
        results = []

        # Initialize simulation at workflow's starting state
        self.simulator.set_initial_states(self.workflow.initial_states)

        for step in self.workflow.steps:
            # Execute the automation step in simulation
            sim_result = self.simulator.execute_action(step.action)

            # Check if step succeeded
            step_result = StepResult(
                step=step,
                simulated_result=sim_result,
                expected_states=step.expected_result_states,
                actual_states=sim_result.resulting_states,
                passed=sim_result.resulting_states == step.expected_result_states
            )
            results.append(step_result)

            if not step_result.passed:
                # Workflow failed at this step
                break

        return WorkflowTestResult(
            workflow=self.workflow,
            step_results=results,
            completed=all(r.passed for r in results),
            failed_at=next((r for r in results if not r.passed), None)
        )
```

### Historical Data Structure

```python
@dataclass
class HistoricalCapture:
    """A single recorded action and its outcome."""
    session_id: str
    timestamp: float
    frame_before: int
    frame_after: int

    # State configuration when action occurred
    active_states_before: Set[str]

    # The action taken
    action_type: str          # "click", "type", "drag", etc.
    action_target: str        # StateImage ID or element ID
    action_params: dict       # Additional action parameters

    # Resulting state configuration
    active_states_after: Set[str]
    states_appeared: Set[str]
    states_disappeared: Set[str]


class HistoricalData:
    """
    Database of historical captures for simulation.
    Built from automation run recordings (video + events).

    Source: Captured videos and data from automation executions,
    NOT just manual capture sessions.
    """

    def find_matching(self,
                      active_states: Set[str],
                      action_type: str,
                      action_target: str) -> HistoricalMatches:
        """
        Find all historical instances where:
        - Same states were active
        - Same action type was performed
        - Same target was acted upon

        Returns ALL matches - caller will select randomly to
        simulate variability of live automation.
        """

    def get_match_count(self, active_states: Set[str],
                        action_type: str,
                        action_target: str) -> int:
        """Return number of historical matches for this action."""

    def import_automation_run(self, run_id: str, video_path: str,
                               events_path: str, processed_states: dict):
        """
        Import data from an automation run into historical database.
        Called after each automation execution completes.
        """
```

### Page Structure: Verify Pages vs. Integration Tests

**Important:** Verify pages and Integration Tests are separate concepts:

- **Verify Pages** - Visualize states using position data from the state structure (no historical data needed)
- **Integration Tests** - Test automation workflows using historical data as simulated environment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PAGE SEPARATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VERIFY PAGES (State Visualization)          INTEGRATION TESTS              │
│  ─────────────────────────────────           ──────────────────             │
│  Uses: State structure position data         Uses: Historical automation    │
│  Purpose: Visualize states as they           Purpose: Test workflow         │
│           appear on screen                            correctness           │
│                                                                             │
│  ┌─────────────────────────────┐             ┌─────────────────────────────┐│
│  │ 1. Verify Individual States │             │ Integration Tests Page      ││
│  │    - Show single state      │             │ - Run workflows against     ││
│  │    - Elements in fixed      │             │   simulated environment     ││
│  │      positions              │             │ - Random match selection    ││
│  │    - No historical data     │             │ - Immediate execution       ││
│  │                             │             │ - Optional visualization    ││
│  ├─────────────────────────────┤             │                             ││
│  │ 2. Verify Workflow States   │             │                             ││
│  │    - Show active states     │             │                             ││
│  │      during workflow        │             │                             ││
│  │    - Multiple states        │             │                             ││
│  │      appearing together     │             │                             ││
│  │    - Elements in fixed      │             │                             ││
│  │      positions              │             │                             ││
│  │    - No historical data     │             │                             ││
│  └─────────────────────────────┘             └─────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Verify Page 1: Individual States

Visualizes individual states with their elements in fixed positions (from state structure).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VERIFY / INDIVIDUAL STATES                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATE LIST                        STATE VISUALIZATION                      │
│  ┌─────────────────────────┐       ┌───────────────────────────────────────┐│
│  │ ► Login Screen          │       │                                       ││
│  │   Dashboard             │       │   ┌─────────────┐                     ││
│  │   Settings              │       │   │ username    │  ← StateImage at    ││
│  │   User Profile          │       │   │   field     │    fixed position   ││
│  │   Checkout              │       │   └─────────────┘    (450, 200)       ││
│  │   ...                   │       │                                       ││
│  └─────────────────────────┘       │   ┌─────────────┐                     ││
│                                    │   │ password    │  ← (450, 260)       ││
│  STATE INFO                        │   │   field     │                     ││
│  ┌─────────────────────────┐       │   └─────────────┘                     ││
│  │ Name: Login Screen      │       │                                       ││
│  │ Elements: 4             │       │   ┌─────────────┐                     ││
│  │ Transitions: 2 outgoing │       │   │  Login Btn  │  ← (450, 340)       ││
│  │              1 incoming │       │   └─────────────┘                     ││
│  └─────────────────────────┘       │                                       ││
│                                    └───────────────────────────────────────┘│
│                                    Position data from state structure       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Verify Page 2: Workflow States (Active States)

Visualizes the set of active states that appear during workflows.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VERIFY / WORKFLOW STATES                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKFLOW: Checkout Flow                    ACTIVE STATES VISUALIZATION     │
│  ┌─────────────────────────────┐            ┌──────────────────────────────┐│
│  │ Step 1: Initial            │            │                              ││
│  │ ► Step 2: Add to Cart      │            │  ┌────────────────────────┐  ││
│  │ Step 3: View Cart          │            │  │    Main Navigation     │  ││
│  │ Step 4: Checkout           │            │  │    (always visible)    │  ││
│  │ Step 5: Payment            │            │  └────────────────────────┘  ││
│  │ Step 6: Confirmation       │            │                              ││
│  └─────────────────────────────┘            │  ┌──────────┐ ┌──────────┐  ││
│                                             │  │ Product  │ │  Cart    │  ││
│  ACTIVE STATES AT STEP 2:                   │  │  Card    │ │ Sidebar  │  ││
│  ┌─────────────────────────────┐            │  │          │ │          │  ││
│  │ ☑ Main Navigation          │            │  │ [Add to  │ │ Items: 2 │  ││
│  │ ☑ Product Card             │            │  │  Cart]   │ │ Total:$49│  ││
│  │ ☑ Cart Sidebar             │            │  └──────────┘ └──────────┘  ││
│  │ ☐ Checkout Form (inactive) │            │                              ││
│  └─────────────────────────────┘            │  Elements shown at fixed     ││
│                                             │  positions from state struct ││
│  [◄ Prev Step]  [Next Step ►]               └──────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Integration Tests Page

Tests automation workflows using historical data. Runs immediately by default.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION TESTS                                              [Run All ▶] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKFLOWS                         EXECUTION                                │
│  ┌─────────────────────────┐       ┌───────────────────────────────────────┐│
│  │ ☑ Login Workflow        │       │ Running: Checkout Workflow            ││
│  │ ☑ Checkout Workflow     │       │ Step 4/7: Click "proceed_btn"         ││
│  │ ☐ Admin Workflow        │       │ Match selected: #847 of 23 available  ││
│  │ ☑ Search Workflow       │       │ ████████████░░░░░░░░ 57%              ││
│  └─────────────────────────┘       └───────────────────────────────────────┘│
│                                                                             │
│  HISTORICAL DATA                   RESULTS                                  │
│  ┌─────────────────────────┐       ┌───────────────────────────────────────┐│
│  │ Automation runs: 156    │       │ ✓ Login Workflow         PASSED       ││
│  │ Total actions: 12,847   │       │   7/7 steps (random matches used)     ││
│  │ State coverage: 94%     │       │                                       ││
│  │ Last run: 3 hours ago   │       │ ✗ Checkout Workflow      FAILED       ││
│  └─────────────────────────┘       │   Step 4/7: unexpected state          ││
│                                    │   [View Details]                      ││
│  VISUALIZATION (optional)          │                                       ││
│  ┌─────────────────────────┐       │ ○ Search Workflow        PENDING      ││
│  │ ○ None (immediate)      │       └───────────────────────────────────────┘│
│  │ ○ Screenshots           │                                               │
│  │ ○ State visualization   │       Note: Each run uses random historical   │
│  │   (fixed positions)     │       matches, making tests vary like live    │
│  └─────────────────────────┘       automation.                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**

1. **Workflow Selection** - Select which automation workflows to test

2. **Historical Data Status** - Shows data from automation runs
   - Number of automation runs imported
   - Total recorded actions
   - State coverage percentage

3. **Immediate Execution** - Tests run immediately by default

4. **Random Match Selection** - Each test uses randomly selected historical matches, making every run different (like live automation)

5. **Optional Visualization Modes:**
   - **None** - Immediate execution, results only
   - **Screenshots** - Show actual screenshots from selected historical matches
   - **State visualization** - Show states with elements at fixed positions (like Verify pages)

### Failure Investigation

When a workflow fails, the user can investigate:

```python
@dataclass
class FailureDetail:
    workflow_id: str
    failed_step: int
    action_attempted: AutomationAction

    # What was expected
    expected_states: Set[str]

    # What simulation produced
    actual_states: Set[str]

    # Historical context
    historical_matches: List[HistoricalCapture]
    consistency_score: float

    # Possible causes
    possible_issues: List[str]  # e.g., "Insufficient historical data",
                                 #       "Inconsistent historical outcomes",
                                 #       "State configuration never seen before"

    # Links to relevant data
    related_video_timestamps: List[Tuple[str, float]]  # (session_id, timestamp)
```

---

## Web Functionality

### 1. Real-Time Automation Viewer

**Endpoint:** `GET /api/v1/automation/stream/{session_id}`

**Features:**
- Live compressed video stream (WebSocket or HLS)
- Real-time action events overlay
- State transition indicators
- Match result highlighting

**UI Components:**
- Video player with event timeline
- Action log panel
- State diagram with current position highlighted

### 2. Manual Capture Viewer

**Endpoint:** `GET /api/v1/capture/session/{session_id}`

**Features:**
- Compressed video playback
- **Input Events Side Panel** - Shows events as they occur during playback:
  - Click location (x, y coordinates, button)
  - Keyboard input (key pressed, modifiers)
  - Drag events (start/end positions, path)
  - Scroll events (direction, delta)
- Input event timeline (clickable to jump to event)
- Frame thumbnails at events
- Request full-size screenshots

**Input Events Side Panel UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│  VIDEO PLAYER                    │  INPUT EVENTS               │
│  ┌─────────────────────────────┐ │  ┌─────────────────────────┐│
│  │                             │ │  │ 00:01.234 🖱 Left Click ││
│  │                             │ │  │   Position: (450, 320)  ││
│  │                             │ │  │   Element: "login_btn"  ││
│  │                             │ │  ├─────────────────────────┤│
│  │                             │ │  │ 00:02.567 ⌨ Key Press   ││
│  │                             │ │  │   Key: "Tab"            ││
│  │                             │ │  │   Modifiers: none       ││
│  │                             │ │  ├─────────────────────────┤│
│  │                             │ │  │ 00:03.891 ⌨ Key Press   ││
│  │                             │ │  │   Key: "admin"          ││
│  │                             │ │  │   Type: text input      ││
│  └─────────────────────────────┘ │  └─────────────────────────┘│
│  ──●────────────────────────────  │                             │
│  00:03.9 / 02:45.0               │  [Filter] [Export]          │
└─────────────────────────────────────────────────────────────────┘
```

**Screenshot Request API:**
```
POST /api/v1/capture/session/{session_id}/screenshots
{
    "filter": {
        "event_types": ["mouse_click"],
        "buttons": ["left"],
        "include_after_delay_ms": 1000,
        "max_count": 20
    }
}

Response:
{
    "request_id": "...",
    "status": "pending"  // Runner will upload requested screenshots
}
```

### 3. State Structure Editor

**Endpoint:** `GET /api/v1/projects/{id}/states`

**Features:**
- View detected states from processing
- Edit state definitions (merge, split, rename)
- View/edit state elements (StateImages, regions)
- Full-size screenshot viewer for cutting images
- Position editor for fixed-position elements

**Data Received from Processing:**
```json
{
    "states": [
        {
            "id": "state_1",
            "name": "Login Screen",
            "source_screenshots": ["frame_0042.png", "frame_0108.png"],
            "elements": [
                {
                    "type": "StateImage",
                    "name": "login_button",
                    "image_data": "base64...",
                    "position": {"x": 450, "y": 320, "fixed": true},
                    "source_region": {"x": 440, "y": 310, "w": 100, "h": 40}
                }
            ]
        }
    ],
    "processing_log": {
        "steps": [...],
        "parameters_used": {...},
        "confidence_scores": {...}
    }
}
```

### 4. Processing Review Interface (Power Tool for qontinui Library Development)

**Endpoint:** `GET /api/v1/capture/session/{session_id}/processing`

The Processing Review Interface is designed as a **powerful tool for improving the processing that occurs in the qontinui library**. This is critical infrastructure for iteratively improving detection accuracy and processing quality.

**Core Features:**
- Step-by-step processing visualization
- Parameter adjustment interface
- Re-run processing with new parameters
- Compare results across parameter sets
- Side-by-side before/after comparison

**Analysis Pipeline Visualization:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROCESSING REVIEW DASHBOARD                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ANALYSIS PIPELINE                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   1. State  │ ─► │  2. Image   │ ─► │ 3. Element  │ ─► │ 4. Transition│ │
│  │  Boundary   │    │  Extraction │    │  Detection  │    │   Analysis  │  │
│  │  Detection  │    │             │    │             │    │             │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     RESULTS VIEWER                                   │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Frame 42 @ 00:01.234                                          │  │   │
│  │  │ ┌─────────────────────┐  State: "Login Screen" (confidence: 0.94)│   │
│  │  │ │    [Screenshot]     │  Elements detected: 5                   │  │   │
│  │  │ │    with overlays    │  ├─ username_field (0.98)               │  │   │
│  │  │ │    showing:         │  ├─ password_field (0.97)               │  │   │
│  │  │ │    - State bounds   │  ├─ login_button (0.99)                 │  │   │
│  │  │ │    - Elements       │  ├─ forgot_password (0.89)              │  │   │
│  │  │ │    - Click location │  └─ remember_me (0.92)                  │  │   │
│  │  │ └─────────────────────┘                                         │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PARAMETER TUNING                          ANNOTATIONS                      │
│  ┌─────────────────────────────┐           ┌─────────────────────────────┐  │
│  │ State Similarity: [0.95 ▼]  │           │ ☑ Correct state detected    │  │
│  │ Min State Duration: [500ms] │           │ ☐ login_button correct      │  │
│  │ Edge Detection: [Canny ▼]   │           │ ☑ forgot_password misaligned│  │
│  │ Clustering: [DBSCAN ▼]      │           │ [Add Note...]               │  │
│  │                             │           │                             │  │
│  │ [Re-run Analysis]           │           │ [Save Annotations]          │  │
│  └─────────────────────────────┘           └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**For Developer Improvement:**
- View edge cases and failures in detail
- Annotate correct/incorrect detections with notes
- Export training data for model improvement
- A/B test different algorithm configurations
- Track improvement metrics over time
- Identify systematic failure patterns

**Annotation Types:**
```python
@dataclass
class ProcessingAnnotation:
    frame_id: str
    annotation_type: str  # "correct", "incorrect", "partial", "edge_case"
    element_id: Optional[str]
    correct_value: Optional[dict]  # Ground truth for incorrect detections
    notes: str
    tags: List[str]  # ["low_contrast", "occlusion", "motion_blur", etc.]
```

**Metrics Dashboard:**
- Detection accuracy by element type
- False positive/negative rates
- Processing time per frame
- Confidence distribution
- Failure categorization

### 5. Verify / Individual States Page

**Endpoint:** `GET /api/v1/projects/{id}/states/verify`

**Purpose:** Visualize individual states with elements at fixed positions (uses state structure, no historical data).

**Features:**
- List all states in project
- Select state to visualize
- Show StateImages at their fixed positions
- Display state metadata (transitions, elements count)

**Data Source:** State structure configuration (position data).

### 6. Verify / Workflow States Page

**Endpoint:** `GET /api/v1/projects/{id}/workflows/{workflow_id}/verify`

**Purpose:** Visualize the set of active states at each step of a workflow.

**Features:**
- Select workflow to visualize
- Step through workflow stages
- Show all active states at each step
- Display elements from all active states at fixed positions
- Navigate forward/backward through steps

**Data Source:** State structure configuration + workflow definition.

### 7. Integration Tests Page

**Endpoint:** `GET /api/v1/projects/{id}/integration-tests`

**Purpose:** Test automation workflows using historical data as simulated environment.

**Features:**
- Select workflows to test
- Run tests immediately (default) or with visualization
- Random selection from historical matches (each run is different)
- View test results and failures
- Historical data statistics (runs, actions, coverage)

**Optional Visualization Modes:**
- None (immediate)
- Screenshots from selected matches
- State visualization (fixed positions)

**Data Stored:**
```json
{
    "run_id": "...",
    "config_version": "...",
    "start_time": "...",
    "end_time": "...",
    "status": "passed|failed",
    "states_visited": [...],
    "actions_executed": [...],
    "failures": [
        {
            "action_id": "...",
            "expected_state": "...",
            "actual_screenshot": "s3://...",
            "error": "..."
        }
    ]
}
```

### 8. Project Tools / Overview Page

**Features:**
- State diagram with element positions
- Coverage visualization
- Element inventory with thumbnails
- Links to Verify pages and Integration Tests

---

## Data Export/Import

### Exported (Configuration File Only)

```json
{
    "version": "2.0",
    "states": [
        {
            "id": "state_1",
            "name": "Login Screen",
            "identifying_images": [
                {
                    "id": "img_1",
                    "data": "base64...",  // Cropped StateImage only
                    "position": {"x": 450, "y": 320, "fixed": true}
                }
            ]
        }
    ],
    "transitions": [...],
    "workflows": [...]
}
```

**NOT exported:** Raw screenshots, video, event logs

### Imported to Web

Users can import from local storage:
- Selected full-size screenshots (for state editing)
- Processed state definitions
- Processing logs (for review)

---

## qontinui-train Integration

**Receives same data as web:**
- Compressed video
- Input events
- Processed states and elements
- Full-size screenshots (for training data)
- Processing logs

**Additional for Training:**
- Annotated correct/incorrect detections
- Edge case examples
- Model performance metrics

---

## Implementation Phases

### Phase 1: Core Video Capture
1. Replace screenshot capture with video recording (FFmpeg H.264)
2. Implement comprehensive input monitoring (mouse: click, drag, scroll, move; keyboard: all keys)
3. Implement timestamp correlation between video frames and input events
4. Local storage management with session organization

### Phase 2: Cloud Streaming
1. Compressed video streaming (720p, 10fps, 1Mbps)
2. Event log streaming (JSONL, gzipped)
3. Thumbnail generation and streaming
4. Full-size screenshot request/response API

### Phase 3: Analysis Pipeline - State Detection
1. Frame extraction service (at input events and intervals)
2. State boundary detection (SSIM clustering, perceptual hashing)
3. Optical flow analysis for transition point detection
4. Processing log generation for review

### Phase 4: Analysis Pipeline - Image & Element Extraction
1. StateImage extraction within state boundaries
2. Click-location-based image extraction
3. UI element detection (YOLO/contour analysis)
4. Fixed vs. dynamic position determination

### Phase 5: Analysis Pipeline - Transition Analysis
1. State change correlation with input events
2. Outgoing action identification (which StateImage was clicked)
3. Incoming recognition identification (which StateImages appeared)
4. Automated transition creation with multi-state support

### Phase 6: Web Integration - Viewers
1. Real-time automation viewer with event overlay
2. Manual capture viewer with input events side panel
3. State structure editor with full-size screenshot support
4. Video playback synchronized with event timeline

### Phase 7: Processing Review Tool
1. Step-by-step pipeline visualization
2. Parameter tuning interface
3. Re-run processing with comparison
4. Annotation system for correct/incorrect detections
5. Metrics dashboard and failure pattern analysis

### Phase 8: Automation Workflow Integration Testing
1. Historical data database (actions + outcomes by state configuration)
2. GUI Simulator using historical data as simulated environment
3. Workflow execution against simulated environment
4. Integration with existing Verify / Integration Tests page
5. Failure investigation with links to source video/frames

### Phase 9: Training Integration
1. qontinui-train data pipeline (video + events + processed data)
2. Annotation export for model training
3. Model feedback loop with metrics
4. Edge case collection and labeling

---

## File Changes Summary

### Remove
- `python-bridge/services/capture_tool_service.py` (screenshot capture)
- `python-bridge/capture_manager.py` (screenshot coordination)

### Modify
- `python-bridge/qontinui_executor.py` - Use video capture instead of screenshots
- `src-tauri/src/video_recorder/` - Dual output support (full quality + compressed)
- `src/components/settings/CaptureSettings.tsx` - Video settings UI

### Add - Core Capture
- `python-bridge/services/video_capture_service.py` - FFmpeg video recording
- `python-bridge/services/input_monitor_service.py` - All input event monitoring
- `python-bridge/services/frame_extractor_service.py` - On-demand frame extraction
- `python-bridge/services/cloud_streaming_service.py` - Compressed streaming to AWS

### Add - Analysis Pipeline
- `python-bridge/analysis/state_boundary_detector.py` - SSIM/clustering state detection
- `python-bridge/analysis/image_extractor.py` - StateImage extraction within boundaries
- `python-bridge/analysis/element_detector.py` - UI element detection (YOLO/contour)
- `python-bridge/analysis/transition_analyzer.py` - Transition identification and creation
- `python-bridge/analysis/pipeline.py` - Combined analysis orchestration

### Add - Automation Integration Testing
- `python-bridge/testing/historical_data.py` - Historical capture database
- `python-bridge/testing/gui_simulator.py` - Simulated environment using historical data
- `python-bridge/testing/workflow_tester.py` - Workflow execution against simulation
- `python-bridge/testing/failure_investigator.py` - Failure analysis with video links

### Add - Models
- `python-bridge/models/input_event.py` - Input event data structures
- `python-bridge/models/extracted_frame.py` - Frame with metadata
- `python-bridge/models/detected_state.py` - State boundary and images
- `python-bridge/models/transition.py` - Transition with outgoing/incoming parts
- `python-bridge/models/processing_result.py` - Analysis results
- `python-bridge/models/test_case.py` - Integration test structures

### Add - Processing Review (qontinui-web)
- `src/pages/ProcessingReview/` - Full processing review interface
- `src/components/AnalysisPipeline/` - Pipeline step visualization
- `src/components/ParameterTuning/` - Parameter adjustment UI
- `src/components/AnnotationTools/` - Correct/incorrect marking
- `src/components/MetricsDashboard/` - Accuracy and performance metrics

### Add - Capture Viewer Enhancements (qontinui-web)
- `src/components/InputEventsSidePanel/` - Events during video playback
- `src/components/EventTimeline/` - Clickable event timeline
- `src/components/TransitionViewer/` - Transition visualization
