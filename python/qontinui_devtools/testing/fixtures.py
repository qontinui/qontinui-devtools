"""Pytest fixtures for Mock HAL components.

This module provides pytest fixtures for easy use of mock HAL components in tests.
"""

import pytest
from PIL import Image

from .mock_hal import MockHAL, MockHALBuilder
from .mock_input_controller import MockInputController
from .mock_ocr_engine import MockOCREngine
from .mock_pattern_matcher import MockPatternMatcher
from .mock_platform_specific import MockPlatformSpecific
from .mock_screen_capture import MockScreenCapture

# Individual component fixtures


@pytest.fixture
def mock_input_controller() -> MockInputController:
    """Provide mock input controller for tests.

    Returns:
        Fresh MockInputController instance
    """
    return MockInputController()


@pytest.fixture
def mock_screen_capture() -> MockScreenCapture:
    """Provide mock screen capture for tests.

    Returns:
        Fresh MockScreenCapture instance
    """
    return MockScreenCapture()


@pytest.fixture
def mock_pattern_matcher() -> MockPatternMatcher:
    """Provide mock pattern matcher for tests.

    Returns:
        Fresh MockPatternMatcher instance
    """
    return MockPatternMatcher()


@pytest.fixture
def mock_ocr_engine() -> MockOCREngine:
    """Provide mock OCR engine for tests.

    Returns:
        Fresh MockOCREngine instance
    """
    return MockOCREngine()


@pytest.fixture
def mock_platform_specific() -> MockPlatformSpecific:
    """Provide mock platform-specific implementation for tests.

    Returns:
        Fresh MockPlatformSpecific instance
    """
    return MockPlatformSpecific()


# Complete HAL fixtures


@pytest.fixture
def mock_hal() -> MockHAL:
    """Provide complete mock HAL for tests.

    Returns:
        Fresh MockHAL instance with default configuration
    """
    return MockHAL.create()


@pytest.fixture
def mock_hal_slow() -> MockHAL:
    """Provide mock HAL with realistic latencies.

    Returns:
        MockHAL with simulated latencies
    """
    return MockHAL.create_slow()


@pytest.fixture
def mock_hal_unreliable() -> MockHAL:
    """Provide mock HAL with simulated failures.

    Returns:
        MockHAL with configured failure rates
    """
    return MockHAL.create_unreliable()


@pytest.fixture
def mock_hal_builder() -> MockHALBuilder:
    """Provide MockHAL builder for custom configurations.

    Returns:
        Fresh MockHALBuilder instance
    """
    return MockHALBuilder()


# Test image fixtures


@pytest.fixture
def test_image() -> Image.Image:
    """Provide simple test image.

    Returns:
        100x100 white PIL Image
    """
    return Image.new("RGB", (100, 100), color="white")


@pytest.fixture
def test_image_with_text() -> Image.Image:
    """Provide test image with text.

    Returns:
        PIL Image with test text
    """
    return MockScreenCapture.create_test_image_with_text(text="Test Button", width=400, height=300)


@pytest.fixture
def test_screenshot() -> Image.Image:
    """Provide full-size test screenshot.

    Returns:
        1920x1080 PIL Image with markers
    """
    return MockScreenCapture._create_test_image(1920, 1080)


@pytest.fixture
def test_pattern() -> Image.Image:
    """Provide test pattern for matching.

    Returns:
        PIL Image with checkerboard pattern
    """
    return MockScreenCapture.create_test_pattern(width=200, height=200, pattern_type="checkerboard")


# Configuration fixtures


@pytest.fixture
def mock_hal_with_test_image(test_screenshot: Image.Image) -> MockHAL:
    """Provide mock HAL with test screenshot configured.

    Args:
        test_screenshot: Test image fixture

    Returns:
        MockHAL with screen capture configured
    """
    hal = MockHAL.create()
    hal.screen_capture.set_test_image(test_screenshot)
    return hal


@pytest.fixture
def mock_hal_with_button(test_image_with_text: Image.Image) -> MockHAL:
    """Provide mock HAL configured to find a button.

    Args:
        test_image_with_text: Test image fixture

    Returns:
        MockHAL with pattern matcher configured to find button
    """
    hal = MockHAL.create()
    hal.screen_capture.set_test_image(test_image_with_text)
    hal.pattern_matcher.configure_match(
        "default", success=True, location=(150, 100), confidence=0.95
    )
    hal.ocr_engine.default_text = "Test Button"
    return hal


# Session-scoped fixtures for expensive setup


@pytest.fixture(scope="session")
def test_images_dir(tmp_path_factory) -> str:  # type: ignore
    """Provide temporary directory for test images.

    Returns:
        Path to temporary directory
    """
    return str(tmp_path_factory.mktemp("test_images"))


# Auto-use fixtures for test isolation


@pytest.fixture(autouse=True)
def reset_mock_hal_between_tests(request: pytest.FixtureRequest) -> None:
    """Automatically reset mock HAL components between tests.

    This fixture runs automatically for every test and ensures
    that any mock HAL instances are reset after each test.
    """
    # Setup: nothing to do before test
    yield
    # Teardown: reset any MockHAL instances used in the test
    # This is automatically handled by creating fresh fixtures each time


# Parametrized fixtures for testing different configurations


@pytest.fixture(params=[0.0, 0.01, 0.1])
def mock_hal_with_latency(request: pytest.FixtureRequest) -> MockHAL:
    """Provide mock HAL with different latency configurations.

    Args:
        request: Pytest request with latency parameter

    Returns:
        MockHAL with specified latency
    """
    latency = request.param
    return MockHAL.create(
        input_latency=latency, screen_latency=latency, pattern_latency=latency, ocr_latency=latency
    )


@pytest.fixture(params=[1.0, 0.95, 0.8])
def mock_hal_with_accuracy(request: pytest.FixtureRequest) -> MockHAL:
    """Provide mock HAL with different accuracy configurations.

    Args:
        request: Pytest request with accuracy parameter

    Returns:
        MockHAL with specified accuracy
    """
    accuracy = request.param
    return MockHAL.create(pattern_success_rate=accuracy, ocr_accuracy=accuracy)


# Context manager fixtures for temporary configuration


@pytest.fixture
def mock_window(mock_platform_specific: MockPlatformSpecific):  # type: ignore
    """Provide a mock window with cleanup.

    Yields:
        Mock Window instance
    """
    window = mock_platform_specific.add_window(
        title="Test Window", x=100, y=100, width=800, height=600
    )
    yield window
    # Cleanup happens automatically when test ends


# Marker-based fixtures


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers.

    Args:
        config: Pytest configuration
    """
    config.addinivalue_line(
        "markers", "mock_hal: mark test as using mock HAL (deselect with '-m \"not mock_hal\"')"
    )
    config.addinivalue_line("markers", "slow_mock: mark test as using slow mock HAL with latencies")
    config.addinivalue_line("markers", "unreliable_mock: mark test as using unreliable mock HAL")
