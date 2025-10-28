# Mock HAL Components

Comprehensive mock implementations of all HAL interfaces for testing without real hardware interaction.

## Overview

The Mock HAL components provide drop-in replacements for qontinui HAL interfaces, allowing you to:

- Test automation workflows without moving the mouse or typing
- Record and verify all input actions
- Configure pattern matching and OCR behavior
- Simulate realistic conditions (latency, failures, accuracy issues)
- Test window management and UI automation

## Quick Start

```python
from qontinui_devtools.testing import MockHAL

# Create mock HAL
hal = MockHAL.create()

# Simulate actions
hal.input_controller.type_text("hello")
hal.input_controller.mouse_click(100, 200)

# Verify actions
assert hal.input_controller.get_typed_text() == ["hello"]
assert hal.input_controller.get_action_count() == 2
```

## Components

### MockInputController

Records all keyboard and mouse actions without performing them.

```python
from qontinui_devtools.testing import MockInputController

controller = MockInputController()

# Perform actions
controller.type_text("username")
controller.mouse_click(200, 300)
controller.hotkey("ctrl", "c")

# Verify actions
assert controller.get_typed_text() == ["username"]
controller.assert_clicked_at(200, 300)
controller.assert_hotkey_pressed("ctrl", "c")

# Get action history
actions = controller.get_actions_by_type("mouse_click")
print(f"Clicks: {len(actions)}")
```

**Features:**
- Records all input actions with timestamps
- Tracks mouse position
- Simulates latency and failures
- Assertion helpers for verification

### MockScreenCapture

Returns configurable test images instead of capturing the screen.

```python
from qontinui_devtools.testing import MockScreenCapture
from PIL import Image

capture = MockScreenCapture()

# Use default test image
screenshot = capture.capture_screen()
assert screenshot.size == (1920, 1080)

# Set custom image
custom_image = Image.new("RGB", (800, 600), color="blue")
capture.set_test_image(custom_image)

# Capture region
region = capture.capture_region(100, 100, 200, 150)
assert region.size == (200, 150)

# Load from file
capture.load_test_image("test_screenshot.png")
```

**Features:**
- Configurable test images
- Region capture support
- Monitor configuration
- Image creation utilities

### MockPatternMatcher

Provides configurable pattern matching behavior.

```python
from qontinui_devtools.testing import MockPatternMatcher
from PIL import Image

matcher = MockPatternMatcher()

# Configure to always succeed at specific location
matcher.configure_match(
    "login_button",
    success=True,
    location=(500, 300),
    confidence=0.98
)

# Configure for specific template image
template = Image.new("RGB", (100, 50))
matcher.configure_match_for_image(
    template,
    success=True,
    location=(500, 300)
)

# Find pattern
haystack = Image.new("RGB", (1920, 1080))
match = matcher.find_pattern(haystack, template)

assert match is not None
assert match.center == (550, 325)  # center of 100x50 at (500, 300)
```

**Features:**
- Configurable match success/failure
- Per-template configuration
- Simulated latency
- Match attempt recording

### MockOCREngine

Provides configurable text extraction.

```python
from qontinui_devtools.testing import MockOCREngine
from PIL import Image

ocr = MockOCREngine(default_text="Login")

# Extract text
image = Image.new("RGB", (400, 300))
text = ocr.extract_text(image)
assert text == "Login"

# Configure text for specific image
ocr.configure_text(image, "Custom Text")
text = ocr.extract_text(image)
assert text == "Custom Text"

# Simulate OCR errors
ocr.set_accuracy(0.9)  # 90% accuracy
text = ocr.extract_text(image)  # May contain errors
```

**Features:**
- Configurable text extraction
- Per-image configuration
- Accuracy simulation
- Text region support
- Find text functionality

### MockPlatformSpecific

Provides mock window management and UI automation.

```python
from qontinui_devtools.testing import MockPlatformSpecific

platform = MockPlatformSpecific()

# Create windows
window = platform.add_window(
    "Test Application",
    x=100, y=100,
    width=800, height=600
)

# Add UI elements
button = platform.add_ui_element(
    window,
    element_type="button",
    name="submit",
    text="Submit",
    x=50, y=50
)

# Find element
found = platform.find_ui_element(window, name="submit")
assert found.text == "Submit"

# Window management
platform.set_window_focus(window)
platform.maximize_window(window)
```

**Features:**
- Window creation and management
- UI element simulation
- Focus management
- Platform information

### MockHAL

Complete HAL container with all mock components.

```python
from qontinui_devtools.testing import MockHAL

# Create with default configuration
hal = MockHAL.create()

# Create with latency
hal = MockHAL.create(
    input_latency=0.01,
    screen_latency=0.05,
    pattern_latency=0.1
)

# Create with failures
hal = MockHAL.create_unreliable()

# Reset all components
hal.reset_all()

# Get operation count
total = hal.get_total_operations()
```

## Builder Pattern

Use `MockHALBuilder` for custom configurations:

```python
from qontinui_devtools.testing import MockHALBuilder

hal = (MockHALBuilder()
    .with_input_latency(0.01)
    .with_pattern_success_rate(0.95)
    .with_ocr_accuracy(0.98)
    .with_ocr_default_text("Custom Text")
    .build())
```

## Pytest Fixtures

Import fixtures in your `conftest.py`:

```python
from qontinui_devtools.testing.fixtures import *
```

Use in tests:

```python
def test_with_mock_hal(mock_hal):
    """Test using mock HAL fixture."""
    mock_hal.input_controller.type_text("test")
    assert mock_hal.input_controller.get_typed_text() == ["test"]

def test_with_custom_image(mock_hal, test_image):
    """Test with custom test image."""
    mock_hal.screen_capture.set_test_image(test_image)
    screenshot = mock_hal.screen_capture.capture_screen()
    assert screenshot.size == test_image.size
```

Available fixtures:
- `mock_hal` - Default mock HAL
- `mock_hal_slow` - With latencies
- `mock_hal_unreliable` - With failures
- `mock_input_controller` - Individual component
- `mock_screen_capture` - Individual component
- `mock_pattern_matcher` - Individual component
- `mock_ocr_engine` - Individual component
- `mock_platform_specific` - Individual component
- `test_image` - Simple test image
- `test_screenshot` - Full-size screenshot
- `test_pattern` - Pattern for matching

## Workflow Testing Example

```python
from qontinui_devtools.testing import MockHAL
from PIL import Image

# Create and configure HAL
hal = MockHAL.create()
hal.pattern_matcher.configure_match(
    "default",
    success=True,
    location=(400, 300)
)
hal.ocr_engine.default_text = "Submit"

# Simulate workflow
screenshot = hal.screen_capture.capture_screen()
button = Image.new("RGB", (100, 40))

# Find and click button
match = hal.pattern_matcher.find_pattern(screenshot, button)
if match:
    hal.input_controller.mouse_click(match.center[0], match.center[1])
    hal.input_controller.type_text("test@example.com")
    hal.input_controller.key_press("enter")

# Verify workflow
assert hal.input_controller.get_action_count() == 3
assert hal.screen_capture.capture_count == 1
```

## Simulating Real-World Conditions

### Latency

```python
hal = MockHAL.create(
    input_latency=0.01,    # 10ms per input
    screen_latency=0.05,   # 50ms per capture
    pattern_latency=0.1,   # 100ms per match
    ocr_latency=0.2        # 200ms per OCR
)
```

### Failures

```python
hal = MockHAL.create(
    input_failure_rate=0.1,      # 10% of inputs fail
    pattern_success_rate=0.9,    # 90% of matches succeed
    ocr_accuracy=0.95            # 95% OCR accuracy
)
```

### Combined

```python
hal = MockHAL.create_unreliable()  # Pre-configured unreliable HAL
```

## Assertion Helpers

```python
controller = MockInputController()

# Perform actions
controller.type_text("hello")
controller.mouse_click(100, 200)
controller.hotkey("ctrl", "s")

# Assert actions occurred
controller.assert_typed_text("hello")
controller.assert_clicked_at(100, 200)
controller.assert_hotkey_pressed("ctrl", "s")
```

## Best Practices

1. **Reset between tests**: Use `hal.reset_all()` or fresh fixtures
2. **Configure before use**: Set up mock behavior before simulating workflows
3. **Verify actions**: Use assertion helpers to verify expected behavior
4. **Simulate realistic conditions**: Add latency and failures for robustness testing
5. **Use fixtures**: Leverage pytest fixtures for consistent test setup

## Performance

Mock HAL components are designed for speed:

- **No actual I/O**: All operations are in-memory
- **Configurable latency**: Add realistic delays when needed
- **Minimal overhead**: Recording actions is very fast
- **Fast by default**: Zero latency unless configured

Typical operation times (without latency):
- Input action: ~0.001ms
- Screen capture: ~1ms
- Pattern match: ~0.01ms
- OCR extraction: ~0.01ms

## API Documentation

See individual module docstrings for detailed API documentation:

- `mock_input_controller.py` - Input control
- `mock_screen_capture.py` - Screen capture
- `mock_pattern_matcher.py` - Pattern matching
- `mock_ocr_engine.py` - OCR
- `mock_platform_specific.py` - Platform-specific
- `mock_hal.py` - HAL container

## Examples

See `examples/test_with_mock_hal.py` for complete examples.

Run examples:
```bash
python examples/test_with_mock_hal.py
```

## Testing

Run tests:
```bash
pytest tests/testing/test_mock_hal.py -v
```

Run with coverage:
```bash
pytest tests/testing/test_mock_hal.py --cov=qontinui_devtools.testing
```

## License

Same as qontinui-devtools parent project.
