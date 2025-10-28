"""Mock HAL components for testing.

This package provides mock implementations of all HAL interfaces,
allowing comprehensive testing without real hardware interaction.

Components:
    - MockInputController: Records keyboard/mouse actions
    - MockScreenCapture: Returns configurable test images
    - MockPatternMatcher: Configurable pattern matching behavior
    - MockOCREngine: Configurable text extraction
    - MockPlatformSpecific: Mock window/UI automation
    - MockHAL: Complete HAL container with all mocks

Example:
    >>> from qontinui_devtools.testing import MockHAL
    >>> hal = MockHAL.create()
    >>> hal.input_controller.type_text("hello")
    >>> assert hal.input_controller.get_typed_text() == ["hello"]

Test Fixtures:
    Import fixtures in conftest.py:
    >>> from qontinui_devtools.testing.fixtures import *
"""

from .mock_hal import MockHAL, MockHALBuilder
from .mock_input_controller import InputAction, MockInputController
from .mock_ocr_engine import MockOCREngine
from .mock_pattern_matcher import MatchConfig, MockPatternMatcher
from .mock_platform_specific import MockPlatformSpecific
from .mock_screen_capture import MockScreenCapture

__all__ = [
    # Main container
    "MockHAL",
    "MockHALBuilder",
    # Individual components
    "MockInputController",
    "MockScreenCapture",
    "MockPatternMatcher",
    "MockOCREngine",
    "MockPlatformSpecific",
    # Helper types
    "InputAction",
    "MatchConfig",
]

__version__ = "0.1.0"
