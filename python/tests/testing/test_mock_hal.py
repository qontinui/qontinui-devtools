"""Tests for Mock HAL components."""

import pytest
from PIL import Image
from qontinui.hal.interfaces import Key, MouseButton
from qontinui_devtools.testing import (
    MockHAL,
    MockHALBuilder,
    MockInputController,
    MockOCREngine,
    MockPatternMatcher,
    MockPlatformSpecific,
    MockScreenCapture,
)
from qontinui_devtools.testing.mock_input_controller import InputControlError


class TestMockInputController:
    """Tests for MockInputController."""

    def test_records_typed_text(self) -> None:
        """Test that input controller records typed text."""
        controller = MockInputController()

        controller.type_text("hello")
        controller.type_text("world")

        assert controller.get_typed_text() == ["hello", "world"]
        assert controller.get_action_count() == 2

    def test_records_mouse_clicks(self) -> None:
        """Test that input controller records mouse clicks."""
        controller = MockInputController()

        controller.mouse_click(100, 200)
        controller.mouse_click(300, 400, button=MouseButton.RIGHT)

        clicks = controller.get_clicks()
        assert len(clicks) == 2
        assert clicks[0]["x"] == 100
        assert clicks[0]["y"] == 200
        assert clicks[1]["button"] == "right"

    def test_tracks_mouse_position(self) -> None:
        """Test that mouse position is tracked."""
        controller = MockInputController()

        controller.mouse_move(500, 300)
        pos = controller.get_mouse_position()

        assert pos.x == 500
        assert pos.y == 300

    def test_key_press_recording(self) -> None:
        """Test that key presses are recorded."""
        controller = MockInputController()

        controller.key_press("a")
        controller.key_press(Key.ENTER)

        actions = controller.get_actions_by_type("key_press")
        assert len(actions) == 2
        assert actions[0].params["key"] == "a"
        assert actions[1].params["key"] == "enter"

    def test_hotkey_recording(self) -> None:
        """Test that hotkey combinations are recorded."""
        controller = MockInputController()

        controller.hotkey("ctrl", "c")

        actions = controller.get_actions_by_type("hotkey")
        assert len(actions) == 1
        assert actions[0].params["keys"] == ["ctrl", "c"]

    def test_assert_clicked_at(self) -> None:
        """Test assertion helper for clicks."""
        controller = MockInputController()
        controller.mouse_click(100, 200)

        # Should not raise
        controller.assert_clicked_at(100, 200)

        # Should raise
        with pytest.raises(AssertionError):
            controller.assert_clicked_at(300, 400)

    def test_simulated_latency(self) -> None:
        """Test that latency is simulated."""
        import time

        controller = MockInputController(latency=0.01)

        start = time.time()
        controller.type_text("test")
        duration = time.time() - start

        assert duration >= 0.01

    def test_simulated_failures(self) -> None:
        """Test simulated failures."""
        controller = MockInputController(failure_rate=1.0, simulate_errors=True)  # Always fail

        with pytest.raises(InputControlError):
            controller.type_text("test")

    def test_reset_clears_actions(self) -> None:
        """Test that reset clears all actions."""
        controller = MockInputController()
        controller.type_text("test")
        controller.mouse_click(100, 200)

        controller.reset()

        assert controller.get_action_count() == 0
        assert controller.get_typed_text() == []


class TestMockScreenCapture:
    """Tests for MockScreenCapture."""

    def test_captures_default_image(self) -> None:
        """Test that default image is captured."""
        capture = MockScreenCapture()

        img = capture.capture_screen()

        assert isinstance(img, Image.Image)
        assert img.size == (1920, 1080)
        assert capture.capture_count == 1

    def test_captures_region(self) -> None:
        """Test region capture."""
        capture = MockScreenCapture()

        img = capture.capture_region(100, 100, 200, 150)

        assert img.size == (200, 150)
        assert len(capture.get_captured_regions()) == 1

    def test_custom_test_image(self) -> None:
        """Test setting custom test image."""
        capture = MockScreenCapture()
        custom_image = Image.new("RGB", (800, 600), color="blue")

        capture.set_test_image(custom_image)
        img = capture.capture_screen()

        assert img.size == (800, 600)

    def test_get_monitors(self) -> None:
        """Test getting monitor list."""
        capture = MockScreenCapture()

        monitors = capture.get_monitors()

        assert len(monitors) == 1
        assert monitors[0].is_primary
        assert monitors[0].width == 1920
        assert monitors[0].height == 1080

    def test_get_pixel_color(self) -> None:
        """Test getting pixel color."""
        capture = MockScreenCapture()

        color = capture.get_pixel_color(100, 100)

        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_save_screenshot(self, tmp_path) -> None:  # type: ignore
        """Test saving screenshot to file."""
        capture = MockScreenCapture()
        filepath = str(tmp_path / "test_screenshot.png")

        saved_path = capture.save_screenshot(filepath)

        assert saved_path == filepath
        assert filepath in capture.get_saved_screenshots()

    def test_reset_clears_history(self) -> None:
        """Test that reset clears capture history."""
        capture = MockScreenCapture()
        capture.capture_screen()
        capture.capture_region(0, 0, 100, 100)

        capture.reset()

        assert capture.capture_count == 0
        assert len(capture.get_captured_regions()) == 0


class TestMockPatternMatcher:
    """Tests for MockPatternMatcher."""

    def test_default_successful_match(self) -> None:
        """Test default successful pattern matching."""
        matcher = MockPatternMatcher(default_success_rate=1.0)
        haystack = Image.new("RGB", (800, 600))
        needle = Image.new("RGB", (50, 50))

        result = matcher.find_pattern(haystack, needle)

        assert result is not None
        assert result.center == (100 + 25, 100 + 25)  # default location + half size

    def test_configured_match(self) -> None:
        """Test configured pattern match."""
        matcher = MockPatternMatcher()

        haystack = Image.new("RGB", (800, 600))
        needle = Image.new("RGB", (50, 50))
        matcher.configure_match_for_image(
            needle, success=True, location=(200, 300), confidence=0.98
        )

        result = matcher.find_pattern(haystack, needle)

        assert result is not None
        assert result.x == 200
        assert result.y == 300
        assert result.confidence == 0.98

    def test_failed_match(self) -> None:
        """Test pattern match failure."""
        matcher = MockPatternMatcher(default_success_rate=0.0)
        haystack = Image.new("RGB", (800, 600))
        needle = Image.new("RGB", (50, 50))

        result = matcher.find_pattern(haystack, needle)

        assert result is None

    def test_find_all_patterns(self) -> None:
        """Test finding all pattern occurrences."""
        matcher = MockPatternMatcher(default_success_rate=1.0)
        haystack = Image.new("RGB", (800, 600))
        needle = Image.new("RGB", (50, 50))

        results = matcher.find_all_patterns(haystack, needle)

        assert isinstance(results, list)
        # Default behavior returns 0-3 matches

    def test_match_attempts_recorded(self) -> None:
        """Test that match attempts are recorded."""
        matcher = MockPatternMatcher()
        haystack = Image.new("RGB", (800, 600))
        needle = Image.new("RGB", (50, 50))

        matcher.find_pattern(haystack, needle)
        matcher.find_all_patterns(haystack, needle)

        attempts = matcher.get_match_attempts()
        assert len(attempts) == 2


class TestMockOCREngine:
    """Tests for MockOCREngine."""

    def test_extracts_default_text(self) -> None:
        """Test extracting default text."""
        ocr = MockOCREngine(default_text="Login")
        image = Image.new("RGB", (400, 300))

        text = ocr.extract_text(image)

        assert text == "Login"

    def test_configured_text_extraction(self) -> None:
        """Test configured text for specific image."""
        ocr = MockOCREngine()
        image = Image.new("RGB", (400, 300))
        ocr.configure_text(image, "Custom Text")

        text = ocr.extract_text(image)

        assert text == "Custom Text"

    def test_get_text_regions(self) -> None:
        """Test getting text regions."""
        ocr = MockOCREngine(default_text="Test")
        image = Image.new("RGB", (400, 300))

        regions = ocr.get_text_regions(image)

        assert len(regions) >= 1
        assert regions[0].text == "Test"

    def test_find_text(self) -> None:
        """Test finding specific text."""
        ocr = MockOCREngine(default_text="Login Button")
        image = Image.new("RGB", (400, 300))

        match = ocr.find_text(image, "Login")

        assert match is not None
        assert "Login" in match.text

    def test_ocr_accuracy_simulation(self) -> None:
        """Test OCR accuracy simulation."""
        ocr = MockOCREngine(default_text="Perfect", accuracy=0.5)
        image = Image.new("RGB", (400, 300))

        text = ocr.extract_text(image)

        # With low accuracy, text may have errors
        assert isinstance(text, str)

    def test_supported_languages(self) -> None:
        """Test getting supported languages."""
        ocr = MockOCREngine()

        languages = ocr.get_supported_languages()

        assert "en" in languages
        assert isinstance(languages, list)

    def test_ocr_calls_recorded(self) -> None:
        """Test that OCR calls are recorded."""
        ocr = MockOCREngine()
        image = Image.new("RGB", (400, 300))

        ocr.extract_text(image)
        ocr.get_text_regions(image)

        calls = ocr.get_ocr_calls()
        # get_text_regions calls extract_text internally, so we get 3 calls total
        assert len(calls) >= 2


class TestMockPlatformSpecific:
    """Tests for MockPlatformSpecific."""

    def test_add_and_get_window(self) -> None:
        """Test adding and retrieving windows."""
        platform = MockPlatformSpecific()
        platform.add_window("Test Window", 100, 100, 800, 600)

        all_windows = platform.get_all_windows()

        assert len(all_windows) == 1
        assert all_windows[0].title == "Test Window"

    def test_get_window_by_title(self) -> None:
        """Test finding window by title."""
        platform = MockPlatformSpecific()
        platform.add_window("My Application", 0, 0, 800, 600)

        window = platform.get_window_by_title("My Application")

        assert window is not None
        assert window.title == "My Application"

    def test_set_window_focus(self) -> None:
        """Test setting window focus."""
        platform = MockPlatformSpecific()
        window = platform.add_window("Test", 0, 0, 800, 600)

        success = platform.set_window_focus(window)
        active = platform.get_active_window()

        assert success
        assert active == window

    def test_window_management(self) -> None:
        """Test window minimize/maximize/restore."""
        platform = MockPlatformSpecific()
        window = platform.add_window("Test", 0, 0, 800, 600)

        platform.minimize_window(window)
        assert window.is_minimized

        platform.maximize_window(window)
        assert window.is_maximized
        assert not window.is_minimized

        platform.restore_window(window)
        assert not window.is_maximized
        assert not window.is_minimized

    def test_add_ui_element(self) -> None:
        """Test adding UI elements to window."""
        platform = MockPlatformSpecific()
        window = platform.add_window("Test", 0, 0, 800, 600)
        platform.add_ui_element(window, element_type="button", name="submit_btn", text="Submit")

        elements = platform.get_ui_elements(window)

        assert len(elements) == 1
        assert elements[0].type == "button"
        assert elements[0].text == "Submit"

    def test_find_ui_element(self) -> None:
        """Test finding UI element."""
        platform = MockPlatformSpecific()
        window = platform.add_window("Test", 0, 0, 800, 600)
        platform.add_ui_element(window, "button", name="submit", text="Submit")

        element = platform.find_ui_element(window, name="submit")

        assert element is not None
        assert element.name == "submit"

    def test_platform_info(self) -> None:
        """Test getting platform information."""
        platform = MockPlatformSpecific(platform_name="TestOS", platform_version="1.2.3")

        assert platform.get_platform_name() == "TestOS"
        assert platform.get_platform_version() == "1.2.3"


class TestMockHAL:
    """Tests for MockHAL container."""

    def test_create_default(self) -> None:
        """Test creating default MockHAL."""
        hal = MockHAL.create()

        assert hal.input_controller is not None
        assert hal.screen_capture is not None
        assert hal.pattern_matcher is not None
        assert hal.ocr_engine is not None
        assert hal.platform_specific is not None

    def test_create_with_latency(self) -> None:
        """Test creating MockHAL with latency."""
        hal = MockHAL.create(input_latency=0.01, screen_latency=0.02)

        assert hal.input_controller.latency == 0.01
        assert hal.screen_capture.latency == 0.02

    def test_create_slow(self) -> None:
        """Test creating slow MockHAL."""
        hal = MockHAL.create_slow()

        assert hal.input_controller.latency > 0
        assert hal.screen_capture.latency > 0

    def test_create_unreliable(self) -> None:
        """Test creating unreliable MockHAL."""
        hal = MockHAL.create_unreliable()

        assert hal.input_controller.failure_rate > 0
        assert hal.pattern_matcher.default_success_rate < 1.0

    def test_reset_all(self) -> None:
        """Test resetting all components."""
        hal = MockHAL.create()

        # Perform some operations
        hal.input_controller.type_text("test")
        hal.screen_capture.capture_screen()

        # Reset
        hal.reset_all()

        assert hal.input_controller.get_action_count() == 0
        assert hal.screen_capture.capture_count == 0

    def test_get_total_operations(self) -> None:
        """Test getting total operation count."""
        hal = MockHAL.create()

        hal.input_controller.type_text("test")
        hal.screen_capture.capture_screen()

        total = hal.get_total_operations()

        assert total >= 2

    def test_builder_pattern(self) -> None:
        """Test MockHALBuilder."""
        hal = (
            MockHALBuilder()
            .with_input_latency(0.01)
            .with_pattern_success_rate(0.95)
            .with_ocr_default_text("Custom Text")
            .build()
        )

        assert hal.input_controller.latency == 0.01
        assert hal.pattern_matcher.default_success_rate == 0.95
        assert hal.ocr_engine.default_text == "Custom Text"


class TestIntegration:
    """Integration tests for Mock HAL."""

    def test_workflow_simulation(self) -> None:
        """Test simulating a complete workflow."""
        hal = MockHAL.create()

        # Configure behavior
        hal.pattern_matcher.configure_match("default", success=True, location=(200, 300))
        hal.ocr_engine.default_text = "Login"

        # Simulate workflow
        screenshot = hal.screen_capture.capture_screen()
        assert screenshot is not None

        text = hal.ocr_engine.extract_text(screenshot)
        assert text == "Login"

        hal.input_controller.mouse_click(200, 300)
        hal.input_controller.type_text("username")

        # Verify actions
        assert hal.input_controller.get_action_count() == 2
        assert hal.screen_capture.capture_count == 1

    def test_pattern_match_and_click(self) -> None:
        """Test finding pattern and clicking it."""
        hal = MockHAL.create()

        # Set up test scenario
        screenshot = hal.screen_capture.capture_screen()
        button = Image.new("RGB", (100, 50))

        hal.pattern_matcher.configure_match_for_image(button, success=True, location=(300, 400))

        # Find and click
        match = hal.pattern_matcher.find_pattern(screenshot, button)
        assert match is not None

        hal.input_controller.mouse_click(match.center[0], match.center[1])

        # Verify click occurred at pattern location
        clicks = hal.input_controller.get_clicks()
        assert len(clicks) == 1
        assert clicks[0]["x"] == match.center[0]
        assert clicks[0]["y"] == match.center[1]
