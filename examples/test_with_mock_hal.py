"""Example: Testing workflows with Mock HAL.

This example demonstrates how to use Mock HAL components to test
automation workflows without real hardware interaction.
"""

from PIL import Image
from qontinui_devtools.testing import MockHAL, MockHALBuilder


def example_basic_usage() -> None:
    """Basic usage of Mock HAL."""
    print("=== Basic Usage ===\n")

    # Create mock HAL
    hal = MockHAL.create()

    # Simulate input actions
    hal.input_controller.type_text("Hello, World!")
    hal.input_controller.mouse_click(100, 200)
    hal.input_controller.hotkey("ctrl", "s")

    # Verify actions
    print(f"Typed text: {hal.input_controller.get_typed_text()}")
    print(f"Total actions: {hal.input_controller.get_action_count()}")
    print(f"Clicks: {len(hal.input_controller.get_clicks())}")


def example_screen_capture() -> None:
    """Example of screen capture testing."""
    print("\n=== Screen Capture ===\n")

    hal = MockHAL.create()

    # Capture screen
    screenshot = hal.screen_capture.capture_screen()
    print(f"Screenshot size: {screenshot.size}")

    # Capture region
    region = hal.screen_capture.capture_region(100, 100, 300, 200)
    print(f"Region size: {region.size}")

    # Check capture count
    print(f"Total captures: {hal.screen_capture.capture_count}")


def example_pattern_matching() -> None:
    """Example of pattern matching testing."""
    print("\n=== Pattern Matching ===\n")

    hal = MockHAL.create()

    # Configure pattern matcher
    hal.pattern_matcher.configure_match(
        "login_button", success=True, location=(500, 300), confidence=0.98
    )

    # Create test images
    screenshot = hal.screen_capture.capture_screen()
    button_template = Image.new("RGB", (100, 50), color="blue")

    # Configure for specific image
    hal.pattern_matcher.configure_match_for_image(
        button_template, success=True, location=(500, 300), confidence=0.98
    )

    # Find pattern
    match = hal.pattern_matcher.find_pattern(screenshot, button_template)

    if match:
        print(f"Pattern found at: ({match.x}, {match.y})")
        print(f"Confidence: {match.confidence}")
        print(f"Center: {match.center}")
    else:
        print("Pattern not found")


def example_ocr_testing() -> None:
    """Example of OCR testing."""
    print("\n=== OCR Testing ===\n")

    hal = MockHAL.create()

    # Set default text
    hal.ocr_engine.default_text = "Login to your account"

    # Extract text
    screenshot = hal.screen_capture.capture_screen()
    text = hal.ocr_engine.extract_text(screenshot)
    print(f"Extracted text: {text}")

    # Configure specific text for an image
    custom_image = Image.new("RGB", (400, 300))
    hal.ocr_engine.configure_text(custom_image, "Custom Button Text")

    text = hal.ocr_engine.extract_text(custom_image)
    print(f"Custom text: {text}")

    # Find specific text
    match = hal.ocr_engine.find_text(screenshot, "Login")
    if match:
        print(f"Found text '{match.text}' at region: {match.region.bounds}")


def example_workflow_testing() -> None:
    """Example of complete workflow testing."""
    print("\n=== Workflow Testing ===\n")

    hal = MockHAL.create()

    # Configure HAL for test scenario
    hal.pattern_matcher.configure_match(
        "default", success=True, location=(400, 300), confidence=0.95
    )
    hal.ocr_engine.default_text = "Submit"

    # Simulate workflow: Find button and click it
    print("Step 1: Capture screen")
    screenshot = hal.screen_capture.capture_screen()

    print("Step 2: Find button using pattern matching")
    button = Image.new("RGB", (100, 40))
    match = hal.pattern_matcher.find_pattern(screenshot, button, confidence=0.9)

    if match:
        print(f"Step 3: Click button at {match.center}")
        hal.input_controller.mouse_click(match.center[0], match.center[1])

        print("Step 4: Type text")
        hal.input_controller.type_text("test@example.com")

        print("Step 5: Press Enter")
        hal.input_controller.key_press("enter")

    # Verify workflow execution
    print("\nWorkflow Results:")
    print(f"  - Total operations: {hal.get_total_operations()}")
    print(f"  - Actions performed: {hal.input_controller.get_action_count()}")
    print(f"  - Screen captures: {hal.screen_capture.capture_count}")
    print(f"  - Pattern matches: {len(hal.pattern_matcher.match_attempts)}")


def example_builder_pattern() -> None:
    """Example using MockHALBuilder."""
    print("\n=== Builder Pattern ===\n")

    # Build custom HAL configuration
    hal = (
        MockHALBuilder()
        .with_input_latency(0.001)
        .with_pattern_success_rate(0.95)
        .with_ocr_accuracy(0.98)
        .with_ocr_default_text("Login Button")
        .build()
    )

    print(f"Input latency: {hal.input_controller.latency}s")
    print(f"Pattern success rate: {hal.pattern_matcher.default_success_rate}")
    print(f"OCR accuracy: {hal.ocr_engine.accuracy}")
    print(f"OCR default text: {hal.ocr_engine.default_text}")


def example_unreliable_conditions() -> None:
    """Example testing with unreliable conditions."""
    print("\n=== Unreliable Conditions ===\n")

    # Create HAL with failures
    hal = MockHAL.create_unreliable()

    print("Testing with unreliable HAL:")
    print(f"  - Input failure rate: {hal.input_controller.failure_rate}")
    print(f"  - Pattern success rate: {hal.pattern_matcher.default_success_rate}")
    print(f"  - OCR accuracy: {hal.ocr_engine.accuracy}")

    # Try operations (some may fail)
    success_count = 0
    for i in range(10):
        if hal.input_controller.type_text(f"test{i}"):
            success_count += 1

    print(f"\nSuccessful operations: {success_count}/10")


def example_assertions() -> None:
    """Example using assertion helpers."""
    print("\n=== Assertion Helpers ===\n")

    hal = MockHAL.create()

    # Perform actions
    hal.input_controller.type_text("username")
    hal.input_controller.mouse_click(200, 300)
    hal.input_controller.hotkey("ctrl", "enter")

    # Use assertion helpers
    try:
        hal.input_controller.assert_typed_text("username")
        print("✓ Typed text assertion passed")

        hal.input_controller.assert_clicked_at(200, 300)
        print("✓ Click position assertion passed")

        hal.input_controller.assert_hotkey_pressed("ctrl", "enter")
        print("✓ Hotkey assertion passed")

    except AssertionError as e:
        print(f"✗ Assertion failed: {e}")


def example_window_management() -> None:
    """Example of window management testing."""
    print("\n=== Window Management ===\n")

    hal = MockHAL.create()

    # Add windows
    window1 = hal.platform_specific.add_window("Browser", x=100, y=100, width=1200, height=800)
    window2 = hal.platform_specific.add_window("Editor", x=200, y=200, width=800, height=600)

    print(f"Created {len(hal.platform_specific.get_all_windows())} windows")

    # Focus window
    hal.platform_specific.set_window_focus(window1)
    active = hal.platform_specific.get_active_window()
    print(f"Active window: {active.title if active else 'None'}")

    # Add UI elements
    button = hal.platform_specific.add_ui_element(
        window1,
        element_type="button",
        name="submit",
        text="Submit",
        x=50,
        y=50,
        width=100,
        height=30,
    )

    print(f"Added button: {button.text}")

    # Find element
    found = hal.platform_specific.find_ui_element(window1, name="submit")
    print(f"Found element: {found.text if found else 'Not found'}")


def example_reset_and_reuse() -> None:
    """Example of resetting and reusing HAL."""
    print("\n=== Reset and Reuse ===\n")

    hal = MockHAL.create()

    # First test
    print("Test 1:")
    hal.input_controller.type_text("test1")
    hal.screen_capture.capture_screen()
    print(f"  Actions: {hal.input_controller.get_action_count()}")
    print(f"  Captures: {hal.screen_capture.capture_count}")

    # Reset
    hal.reset_all()

    # Second test
    print("\nTest 2 (after reset):")
    hal.input_controller.type_text("test2")
    hal.screen_capture.capture_screen()
    print(f"  Actions: {hal.input_controller.get_action_count()}")
    print(f"  Captures: {hal.screen_capture.capture_count}")


def main() -> None:
    """Run all examples."""
    print("Mock HAL Examples\n" + "=" * 50)

    example_basic_usage()
    example_screen_capture()
    example_pattern_matching()
    example_ocr_testing()
    example_workflow_testing()
    example_builder_pattern()
    example_unreliable_conditions()
    example_assertions()
    example_window_management()
    example_reset_and_reuse()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()
