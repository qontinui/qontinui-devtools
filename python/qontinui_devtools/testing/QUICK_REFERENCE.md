# Mock HAL Quick Reference

## Installation

```python
from qontinui_devtools.testing import MockHAL
```

## Quick Start (30 seconds)

```python
# Create mock HAL
hal = MockHAL.create()

# Simulate actions
hal.input_controller.type_text("hello")
hal.input_controller.mouse_click(100, 200)

# Verify
assert hal.input_controller.get_typed_text() == ["hello"]
```

## Common Patterns

### 1. Basic Test

```python
def test_workflow(mock_hal):
    mock_hal.input_controller.type_text("test")
    assert mock_hal.input_controller.get_action_count() == 1
```

### 2. Configure Pattern Match

```python
hal.pattern_matcher.configure_match(
    "default",
    success=True,
    location=(400, 300),
    confidence=0.95
)
```

### 3. Configure OCR Text

```python
hal.ocr_engine.default_text = "Login"
# or
hal.ocr_engine.configure_text(image, "Custom Text")
```

### 4. Custom Test Image

```python
hal.screen_capture.set_test_image(custom_image)
```

### 5. Assert Actions

```python
controller.assert_clicked_at(100, 200)
controller.assert_typed_text("hello")
controller.assert_hotkey_pressed("ctrl", "c")
```

### 6. Reset Between Tests

```python
hal.reset_all()
```

### 7. Builder Pattern

```python
hal = (MockHALBuilder()
    .with_input_latency(0.01)
    .with_pattern_success_rate(0.95)
    .build())
```

### 8. Unreliable Conditions

```python
hal = MockHAL.create_unreliable()
```

### 9. Get Action History

```python
typed = hal.input_controller.get_typed_text()
clicks = hal.input_controller.get_clicks()
actions = hal.input_controller.get_actions_by_type("mouse_click")
```

### 10. Window Management

```python
window = hal.platform_specific.add_window("Test", 100, 100, 800, 600)
button = hal.platform_specific.add_ui_element(window, "button", text="OK")
```

## Pytest Fixtures

```python
# In conftest.py
from qontinui_devtools.testing.fixtures import *

# In test
def test_something(mock_hal, test_image):
    mock_hal.screen_capture.set_test_image(test_image)
```

## Available Fixtures

- `mock_hal` - Complete HAL (fast & reliable)
- `mock_hal_slow` - With latencies
- `mock_hal_unreliable` - With failures
- `mock_input_controller` - Just input
- `mock_screen_capture` - Just screen
- `mock_pattern_matcher` - Just patterns
- `mock_ocr_engine` - Just OCR
- `mock_platform_specific` - Just platform
- `test_image` - 100x100 white image
- `test_screenshot` - 1920x1080 test image
- `test_pattern` - Checkerboard pattern

## Configuration Options

### Latency
```python
MockHAL.create(
    input_latency=0.01,    # seconds
    screen_latency=0.05,
    pattern_latency=0.1,
    ocr_latency=0.2
)
```

### Failures
```python
MockHAL.create(
    input_failure_rate=0.1,      # 10% fail
    pattern_success_rate=0.9,    # 90% succeed
    ocr_accuracy=0.95            # 95% accurate
)
```

## Cheat Sheet

| Task | Code |
|------|------|
| Create HAL | `hal = MockHAL.create()` |
| Type text | `hal.input_controller.type_text("test")` |
| Click mouse | `hal.input_controller.mouse_click(x, y)` |
| Press key | `hal.input_controller.key_press("enter")` |
| Hotkey | `hal.input_controller.hotkey("ctrl", "c")` |
| Capture screen | `hal.screen_capture.capture_screen()` |
| Find pattern | `hal.pattern_matcher.find_pattern(img, tpl)` |
| Extract OCR | `hal.ocr_engine.extract_text(image)` |
| Get actions | `hal.input_controller.get_action_count()` |
| Reset all | `hal.reset_all()` |

## Common Assertions

```python
# Input
controller.assert_clicked_at(x, y)
controller.assert_typed_text("text")
controller.assert_key_pressed("key")
controller.assert_hotkey_pressed("ctrl", "c")

# Counts
assert hal.input_controller.get_action_count() == 3
assert hal.screen_capture.capture_count == 1
assert len(hal.pattern_matcher.match_attempts) > 0
```

## Test Template

```python
def test_my_workflow(mock_hal):
    """Test description."""
    # Configure
    mock_hal.pattern_matcher.configure_match(
        "default", True, (400, 300)
    )
    mock_hal.ocr_engine.default_text = "Login"

    # Execute
    screenshot = mock_hal.screen_capture.capture_screen()
    match = mock_hal.pattern_matcher.find_pattern(
        screenshot, template
    )
    mock_hal.input_controller.mouse_click(
        match.center[0], match.center[1]
    )

    # Verify
    assert mock_hal.input_controller.get_action_count() == 1
    mock_hal.input_controller.assert_clicked_at(
        match.center[0], match.center[1]
    )
```

## Tips

1. **Always reset**: Use `hal.reset_all()` or fresh fixtures
2. **Configure first**: Set up behavior before using
3. **Use assertions**: Better error messages
4. **Test failures**: Use unreliable HAL for robustness
5. **Check coverage**: Verify all actions performed

## Examples

See `examples/test_with_mock_hal.py` for complete working examples.

Run:
```bash
python examples/test_with_mock_hal.py
```

## Documentation

Full documentation: `python/qontinui_devtools/testing/README.md`
