"""Mock implementation of IPlatformSpecific for testing.

This module provides a mock platform-specific implementation with configurable
window and UI element behavior for testing without actual platform interaction.
"""

import time
from typing import Any

from qontinui.hal.interfaces import IPlatformSpecific
from qontinui.hal.interfaces.platform_specific import UIElement, Window


class MockPlatformSpecific(IPlatformSpecific):
    """Mock implementation of IPlatformSpecific.

    This mock provides configurable window and UI automation behavior for testing.
    Allows simulating window management and UI interaction without real platform APIs.

    Attributes:
        windows: List of mock windows
        active_window: Currently active window
        platform_name: Mock platform name
        platform_version: Mock platform version
        latency: Simulated operation latency

    Example:
        >>> platform = MockPlatformSpecific()
        >>> window = platform.add_window("Test Window", 100, 100, 800, 600)
        >>> platform.set_window_focus(window)
        >>> assert platform.get_active_window() == window
    """

    def __init__(
        self,
        platform_name: str = "MockOS",
        platform_version: str = "1.0.0",
        screen_resolution: tuple[int, int] = (1920, 1080),
        dpi_scaling: float = 1.0,
        dark_mode: bool = False,
        latency: float = 0.0,
    ) -> None:
        """Initialize mock platform-specific implementation.

        Args:
            platform_name: Mock platform name
            platform_version: Mock platform version
            screen_resolution: Screen resolution (width, height)
            dpi_scaling: DPI scaling factor
            dark_mode: Whether dark mode is enabled
            latency: Simulated operation latency in seconds
        """
        self.windows: list[Window] = []
        self.active_window: Window | None = None
        self._platform_name = platform_name
        self._platform_version = platform_version
        self._screen_resolution = screen_resolution
        self._dpi_scaling = dpi_scaling
        self._dark_mode = dark_mode
        self.latency = latency
        self._ui_elements: dict[Any, list[UIElement]] = {}  # window handle → elements
        self._next_handle = 1

    def _simulate_latency(self) -> None:
        """Simulate operation latency."""
        if self.latency > 0:
            time.sleep(self.latency)

    def _get_next_handle(self) -> int:
        """Get next unique handle."""
        handle = self._next_handle
        self._next_handle += 1
        return handle

    # Window management

    def get_all_windows(self) -> list[Window]:
        """Get list of all windows."""
        self._simulate_latency()
        return self.windows.copy()

    def get_window_by_title(self, title: str, partial: bool = False) -> Window | None:
        """Find window by title.

        Args:
            title: Window title to search for
            partial: Allow partial title match

        Returns:
            Window if found, None otherwise
        """
        self._simulate_latency()
        for window in self.windows:
            if partial:
                if title.lower() in window.title.lower():
                    return window
            else:
                if window.title == title:
                    return window
        return None

    def get_window_by_process(self, process_name: str) -> list[Window]:
        """Get windows belonging to a process.

        Args:
            process_name: Process name

        Returns:
            List of Window objects
        """
        self._simulate_latency()
        # In mock, we don't track process names, so return empty list
        return []

    def get_active_window(self) -> Window | None:
        """Get currently active/focused window."""
        self._simulate_latency()
        return self.active_window

    def set_window_focus(self, window: Window) -> bool:
        """Set focus to window.

        Args:
            window: Window to focus

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            self.active_window = window
            return True
        return False

    def minimize_window(self, window: Window) -> bool:
        """Minimize window.

        Args:
            window: Window to minimize

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            window.is_minimized = True
            window.is_maximized = False
            return True
        return False

    def maximize_window(self, window: Window) -> bool:
        """Maximize window.

        Args:
            window: Window to maximize

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            window.is_maximized = True
            window.is_minimized = False
            # Set to screen size
            window.x = 0
            window.y = 0
            window.width = self._screen_resolution[0]
            window.height = self._screen_resolution[1]
            return True
        return False

    def restore_window(self, window: Window) -> bool:
        """Restore window to normal size.

        Args:
            window: Window to restore

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            window.is_minimized = False
            window.is_maximized = False
            return True
        return False

    def move_window(self, window: Window, x: int, y: int) -> bool:
        """Move window to position.

        Args:
            window: Window to move
            x: Target X coordinate
            y: Target Y coordinate

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            window.x = x
            window.y = y
            return True
        return False

    def resize_window(self, window: Window, width: int, height: int) -> bool:
        """Resize window.

        Args:
            window: Window to resize
            width: New width
            height: New height

        Returns:
            True if successful
        """
        self._simulate_latency()
        if window in self.windows:
            window.width = width
            window.height = height
            return True
        return False

    # UI Automation

    def get_ui_elements(self, window: Window) -> list[UIElement]:
        """Get all UI elements in window.

        Args:
            window: Window to analyze

        Returns:
            List of UIElement objects
        """
        self._simulate_latency()
        return self._ui_elements.get(window.handle, []).copy()

    def find_ui_element(
        self,
        window: Window,
        name: str | None = None,
        type: str | None = None,
        text: str | None = None,
    ) -> UIElement | None:
        """Find UI element by properties.

        Args:
            window: Window to search in
            name: Element name/ID
            type: Element type
            text: Element text content

        Returns:
            UIElement if found, None otherwise
        """
        self._simulate_latency()
        elements = self._ui_elements.get(window.handle, [])

        for element in elements:
            matches = True
            if name is not None and element.name != name:
                matches = False
            if type is not None and element.type != type:
                matches = False
            if text is not None and element.text != text:
                matches = False

            if matches:
                return element

        return None

    def click_ui_element(self, element: UIElement) -> bool:
        """Click UI element using platform API.

        Args:
            element: Element to click

        Returns:
            True if successful
        """
        self._simulate_latency()
        if element.is_enabled and element.is_visible:
            return True
        return False

    def set_ui_text(self, element: UIElement, text: str) -> bool:
        """Set text in UI element.

        Args:
            element: Text input element
            text: Text to set

        Returns:
            True if successful
        """
        self._simulate_latency()
        if element.is_enabled and element.is_visible:
            element.text = text
            return True
        return False

    def get_ui_text(self, element: UIElement) -> str | None:
        """Get text from UI element.

        Args:
            element: Element to read from

        Returns:
            Text content or None
        """
        self._simulate_latency()
        return element.text

    # System information

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self._platform_name

    def get_platform_version(self) -> str:
        """Get platform version."""
        return self._platform_version

    def get_screen_resolution(self) -> tuple[int, int]:
        """Get primary screen resolution."""
        return self._screen_resolution

    def get_dpi_scaling(self) -> float:
        """Get DPI scaling factor."""
        return self._dpi_scaling

    def is_dark_mode(self) -> bool:
        """Check if system is in dark mode."""
        return self._dark_mode

    # Test helper methods

    def add_window(
        self,
        title: str,
        x: int = 0,
        y: int = 0,
        width: int = 800,
        height: int = 600,
        class_name: str | None = None,
        process_id: int | None = None,
        is_visible: bool = True,
    ) -> Window:
        """Add a mock window.

        Args:
            title: Window title
            x: X position
            y: Y position
            width: Width
            height: Height
            class_name: Window class name
            process_id: Process ID
            is_visible: Whether window is visible

        Returns:
            Created Window object
        """
        window = Window(
            handle=self._get_next_handle(),
            title=title,
            class_name=class_name,
            process_id=process_id,
            x=x,
            y=y,
            width=width,
            height=height,
            is_visible=is_visible,
            is_minimized=False,
            is_maximized=False,
        )
        self.windows.append(window)
        self._ui_elements[window.handle] = []
        return window

    def remove_window(self, window: Window) -> bool:
        """Remove a window.

        Args:
            window: Window to remove

        Returns:
            True if removed
        """
        if window in self.windows:
            self.windows.remove(window)
            if window == self.active_window:
                self.active_window = None
            if window.handle in self._ui_elements:
                del self._ui_elements[window.handle]
            return True
        return False

    def add_ui_element(
        self,
        window: Window,
        element_type: str,
        name: str | None = None,
        text: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 100,
        height: int = 30,
        is_enabled: bool = True,
        is_visible: bool = True,
    ) -> UIElement:
        """Add a UI element to a window.

        Args:
            window: Window containing element
            element_type: Element type (button, textbox, etc.)
            name: Element name/ID
            text: Element text
            x: X position relative to window
            y: Y position relative to window
            width: Width
            height: Height
            is_enabled: Whether enabled
            is_visible: Whether visible

        Returns:
            Created UIElement
        """
        element = UIElement(
            handle=self._get_next_handle(),
            type=element_type,
            name=name,
            text=text,
            class_name=None,
            x=window.x + x,
            y=window.y + y,
            width=width,
            height=height,
            is_enabled=is_enabled,
            is_visible=is_visible,
            is_focused=False,
        )

        if window.handle not in self._ui_elements:
            self._ui_elements[window.handle] = []

        self._ui_elements[window.handle].append(element)
        return element

    def set_screen_resolution(self, width: int, height: int) -> None:
        """Set screen resolution.

        Args:
            width: Screen width
            height: Screen height
        """
        self._screen_resolution = (width, height)

    def set_dpi_scaling(self, scaling: float) -> None:
        """Set DPI scaling factor.

        Args:
            scaling: DPI scaling factor
        """
        self._dpi_scaling = scaling

    def set_dark_mode(self, enabled: bool) -> None:
        """Set dark mode state.

        Args:
            enabled: Whether dark mode is enabled
        """
        self._dark_mode = enabled

    def reset(self) -> None:
        """Clear all windows and reset state."""
        self.windows.clear()
        self.active_window = None
        self._ui_elements.clear()
        self._next_handle = 1
