"""Mock HAL container for testing.

This module provides a complete mock HAL implementation that can be used
as a drop-in replacement for the real HAL container in tests.
"""

from dataclasses import dataclass

from qontinui.hal import HALConfig

from .mock_input_controller import MockInputController
from .mock_ocr_engine import MockOCREngine
from .mock_pattern_matcher import MockPatternMatcher
from .mock_platform_specific import MockPlatformSpecific
from .mock_screen_capture import MockScreenCapture


@dataclass
class MockHAL:
    """Complete mock HAL container.

    This container provides mock implementations of all HAL interfaces,
    allowing complete workflow testing without hardware interaction.

    Attributes:
        input_controller: Mock input controller
        screen_capture: Mock screen capture
        pattern_matcher: Mock pattern matcher
        ocr_engine: Mock OCR engine
        platform_specific: Mock platform-specific implementation
        config: HAL configuration (optional)

    Example:
        >>> hal = MockHAL.create()
        >>> hal.input_controller.type_text("test")
        >>> assert hal.input_controller.get_typed_text() == ["test"]
        >>> hal.reset_all()
    """

    input_controller: MockInputController
    screen_capture: MockScreenCapture
    pattern_matcher: MockPatternMatcher
    ocr_engine: MockOCREngine
    platform_specific: MockPlatformSpecific
    config: HALConfig | None = None

    @classmethod
    def create(
        cls,
        input_latency: float = 0.0,
        input_failure_rate: float = 0.0,
        screen_latency: float = 0.0,
        pattern_latency: float = 0.0,
        pattern_success_rate: float = 1.0,
        ocr_latency: float = 0.0,
        ocr_accuracy: float = 1.0,
        platform_latency: float = 0.0,
        config: HALConfig | None = None,
    ) -> "MockHAL":
        """Create mock HAL with default configuration.

        Args:
            input_latency: Input operation latency in seconds
            input_failure_rate: Input failure rate (0.0-1.0)
            screen_latency: Screen capture latency in seconds
            pattern_latency: Pattern matching latency in seconds
            pattern_success_rate: Pattern match success rate (0.0-1.0)
            ocr_latency: OCR processing latency in seconds
            ocr_accuracy: OCR accuracy (0.0-1.0)
            platform_latency: Platform operation latency in seconds
            config: Optional HAL configuration

        Returns:
            Configured MockHAL instance

        Example:
            >>> hal = MockHAL.create(
            ...     input_latency=0.001,
            ...     pattern_success_rate=0.95
            ... )
        """
        return cls(
            input_controller=MockInputController(
                latency=input_latency, failure_rate=input_failure_rate
            ),
            screen_capture=MockScreenCapture(latency=screen_latency),
            pattern_matcher=MockPatternMatcher(
                default_success_rate=pattern_success_rate, latency=pattern_latency
            ),
            ocr_engine=MockOCREngine(accuracy=ocr_accuracy, latency=ocr_latency),
            platform_specific=MockPlatformSpecific(latency=platform_latency),
            config=config or HALConfig(),
        )

    @classmethod
    def create_slow(cls) -> "MockHAL":
        """Create mock HAL with simulated slow operations.

        Returns:
            MockHAL with latency configured

        Example:
            >>> hal = MockHAL.create_slow()
            >>> # Operations will have realistic delays
        """
        return cls.create(
            input_latency=0.01,  # 10ms
            screen_latency=0.05,  # 50ms
            pattern_latency=0.1,  # 100ms
            ocr_latency=0.2,  # 200ms
            platform_latency=0.01,  # 10ms
        )

    @classmethod
    def create_unreliable(cls) -> "MockHAL":
        """Create mock HAL with simulated unreliable operations.

        Returns:
            MockHAL with failures configured

        Example:
            >>> hal = MockHAL.create_unreliable()
            >>> # Operations may occasionally fail
        """
        return cls.create(
            input_failure_rate=0.1,  # 10% failure rate
            pattern_success_rate=0.8,  # 80% success rate
            ocr_accuracy=0.9,  # 90% accuracy
        )

    @classmethod
    def create_fast_and_reliable(cls) -> "MockHAL":
        """Create mock HAL optimized for fast, reliable testing.

        Returns:
            MockHAL with no latency or failures

        Example:
            >>> hal = MockHAL.create_fast_and_reliable()
            >>> # Operations complete instantly and never fail
        """
        return cls.create()

    def reset_all(self) -> None:
        """Reset all mock components to initial state.

        Clears all recorded actions, captured images, match attempts, etc.
        """
        self.input_controller.reset()
        self.screen_capture.reset()
        self.pattern_matcher.reset()
        self.ocr_engine.reset()
        self.platform_specific.reset()

    def get_total_operations(self) -> int:
        """Get total number of operations performed across all components.

        Returns:
            Total operation count
        """
        return (
            self.input_controller.get_action_count()
            + self.screen_capture.capture_count
            + len(self.pattern_matcher.match_attempts)
            + len(self.ocr_engine.ocr_calls)
        )

    def cleanup(self) -> None:
        """Clean up HAL component resources.

        This method matches the signature of HALContainer.cleanup()
        for compatibility.
        """
        # Mock components don't need cleanup, but provide this for compatibility
        pass


class MockHALBuilder:
    """Builder for creating customized MockHAL instances.

    Example:
        >>> hal = (MockHALBuilder()
        ...     .with_input_latency(0.01)
        ...     .with_pattern_success_rate(0.95)
        ...     .with_default_test_image()
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize builder with default values."""
        self._input_latency = 0.0
        self._input_failure_rate = 0.0
        self._screen_latency = 0.0
        self._pattern_latency = 0.0
        self._pattern_success_rate = 1.0
        self._ocr_latency = 0.0
        self._ocr_accuracy = 1.0
        self._ocr_default_text = "Mock OCR Text"
        self._platform_latency = 0.0
        self._test_image = None
        self._config = None

    def with_input_latency(self, latency: float) -> "MockHALBuilder":
        """Set input operation latency."""
        self._input_latency = latency
        return self

    def with_input_failure_rate(self, rate: float) -> "MockHALBuilder":
        """Set input failure rate."""
        self._input_failure_rate = rate
        return self

    def with_screen_latency(self, latency: float) -> "MockHALBuilder":
        """Set screen capture latency."""
        self._screen_latency = latency
        return self

    def with_pattern_latency(self, latency: float) -> "MockHALBuilder":
        """Set pattern matching latency."""
        self._pattern_latency = latency
        return self

    def with_pattern_success_rate(self, rate: float) -> "MockHALBuilder":
        """Set pattern match success rate."""
        self._pattern_success_rate = rate
        return self

    def with_ocr_latency(self, latency: float) -> "MockHALBuilder":
        """Set OCR processing latency."""
        self._ocr_latency = latency
        return self

    def with_ocr_accuracy(self, accuracy: float) -> "MockHALBuilder":
        """Set OCR accuracy."""
        self._ocr_accuracy = accuracy
        return self

    def with_ocr_default_text(self, text: str) -> "MockHALBuilder":
        """Set default OCR text."""
        self._ocr_default_text = text
        return self

    def with_platform_latency(self, latency: float) -> "MockHALBuilder":
        """Set platform operation latency."""
        self._platform_latency = latency
        return self

    def with_test_image(self, image) -> "MockHALBuilder":  # type: ignore
        """Set test image for screen capture."""
        self._test_image = image
        return self

    def with_default_test_image(self) -> "MockHALBuilder":
        """Use default test image for screen capture."""
        self._test_image = None  # Will use MockScreenCapture default
        return self

    def with_config(self, config: HALConfig) -> "MockHALBuilder":
        """Set HAL configuration."""
        self._config = config
        return self

    def build(self) -> MockHAL:
        """Build the MockHAL instance.

        Returns:
            Configured MockHAL instance
        """
        hal = MockHAL.create(
            input_latency=self._input_latency,
            input_failure_rate=self._input_failure_rate,
            screen_latency=self._screen_latency,
            pattern_latency=self._pattern_latency,
            pattern_success_rate=self._pattern_success_rate,
            ocr_latency=self._ocr_latency,
            ocr_accuracy=self._ocr_accuracy,
            platform_latency=self._platform_latency,
            config=self._config,
        )

        # Set custom OCR text if specified
        if self._ocr_default_text != "Mock OCR Text":
            hal.ocr_engine.default_text = self._ocr_default_text

        # Set test image if specified
        if self._test_image is not None:
            hal.screen_capture.set_test_image(self._test_image)

        return hal
