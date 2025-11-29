"""Mock implementation of IInputController for testing.

This module provides a mock input controller that records all input actions
without actually performing them. Useful for testing workflows without
hardware interaction.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Any

from qontinui.hal.interfaces import IInputController, Key, MouseButton
from qontinui.hal.interfaces.input_controller import MousePosition


@dataclass
class InputAction:
    """Record of an input action.

    Attributes:
        action_type: Type of action (e.g., "type", "click", "move")
        timestamp: When the action occurred
        params: Dictionary of action parameters
    """

    action_type: str
    timestamp: float
    params: dict[str, Any] = field(default_factory=dict)


class InputControlError(Exception):
    """Exception raised when simulated input failure occurs."""

    pass


class MockInputController(IInputController):
    """Mock implementation of IInputController.

    This mock records all input actions and allows configuration of
    simulated latency, failure rate, and error conditions for testing.

    Attributes:
        actions: List of all recorded input actions
        latency: Simulated latency in seconds (default: 0.0)
        failure_rate: Probability of simulated failure (0.0-1.0, default: 0.0)
        simulate_errors: Whether to raise errors on failure (default: False)

    Example:
        >>> controller = MockInputController()
        >>> controller.type_text("hello")
        >>> controller.mouse_click(100, 200)
        >>> assert len(controller.actions) == 2
        >>> assert controller.get_typed_text() == ["hello"]
    """

    def __init__(
        self, latency: float = 0.0, failure_rate: float = 0.0, simulate_errors: bool = False
    ) -> None:
        """Initialize mock input controller.

        Args:
            latency: Simulated latency for all operations in seconds
            failure_rate: Probability of operation failure (0.0-1.0)
            simulate_errors: If True, raise InputControlError on simulated failures
        """
        self.actions: list[InputAction] = []
        self.latency = latency
        self.failure_rate = failure_rate
        self.simulate_errors = simulate_errors
        self._call_count = 0
        self._mouse_position = MousePosition(x=0, y=0)
        self._pressed_keys: set[str] = set()

    def _should_fail(self) -> bool:
        """Determine if this operation should fail."""
        self._call_count += 1
        return random.random() < self.failure_rate

    def _simulate_latency(self) -> None:
        """Simulate operation latency."""
        if self.latency > 0:
            time.sleep(self.latency)

    def _record_action(self, action_type: str, **params: Any) -> None:
        """Record an action."""
        self.actions.append(
            InputAction(action_type=action_type, timestamp=time.time(), params=params)
        )

    def _check_failure(self) -> bool:
        """Check for failure and handle accordingly."""
        if self._should_fail():
            if self.simulate_errors:
                raise InputControlError("Simulated input failure")
            return False
        return True

    # Mouse operations

    def mouse_move(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse to absolute position."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        self._mouse_position = MousePosition(x=x, y=y)
        self._record_action("mouse_move", x=x, y=y, duration=duration)
        return True

    def mouse_move_relative(self, dx: int, dy: int, duration: float = 0.0) -> bool:
        """Move mouse relative to current position."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        new_x = self._mouse_position.x + dx
        new_y = self._mouse_position.y + dy
        self._mouse_position = MousePosition(x=new_x, y=new_y)
        self._record_action("mouse_move_relative", dx=dx, dy=dy, duration=duration)
        return True

    def mouse_click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        interval: float = 0.0,
    ) -> bool:
        """Click mouse button."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        # Update position if specified
        if x is not None and y is not None:
            self._mouse_position = MousePosition(x=x, y=y)

        self._record_action(
            "mouse_click",
            x=self._mouse_position.x,
            y=self._mouse_position.y,
            button=button.value,
            clicks=clicks,
            interval=interval,
        )
        return True

    def mouse_down(
        self, x: int | None = None, y: int | None = None, button: MouseButton = MouseButton.LEFT
    ) -> bool:
        """Press and hold mouse button."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        if x is not None and y is not None:
            self._mouse_position = MousePosition(x=x, y=y)

        self._record_action(
            "mouse_down", x=self._mouse_position.x, y=self._mouse_position.y, button=button.value
        )
        return True

    def mouse_up(
        self, x: int | None = None, y: int | None = None, button: MouseButton = MouseButton.LEFT
    ) -> bool:
        """Release mouse button."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        if x is not None and y is not None:
            self._mouse_position = MousePosition(x=x, y=y)

        self._record_action(
            "mouse_up", x=self._mouse_position.x, y=self._mouse_position.y, button=button.value
        )
        return True

    def mouse_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: MouseButton = MouseButton.LEFT,
        duration: float = 0.5,
    ) -> bool:
        """Drag mouse from start to end position."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        self._mouse_position = MousePosition(x=end_x, y=end_y)
        self._record_action(
            "mouse_drag",
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button.value,
            duration=duration,
        )
        return True

    def mouse_scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> bool:
        """Scroll mouse wheel."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        if x is not None and y is not None:
            self._mouse_position = MousePosition(x=x, y=y)

        self._record_action(
            "mouse_scroll", clicks=clicks, x=self._mouse_position.x, y=self._mouse_position.y
        )
        return True

    def get_mouse_position(self) -> MousePosition:
        """Get current mouse position."""
        return self._mouse_position

    def click_at(self, x: int, y: int, button: MouseButton = MouseButton.LEFT) -> bool:
        """Click at specific coordinates."""
        return self.mouse_click(x=x, y=y, button=button, clicks=1)

    def double_click_at(self, x: int, y: int, button: MouseButton = MouseButton.LEFT) -> bool:
        """Double click at specific coordinates."""
        return self.mouse_click(x=x, y=y, button=button, clicks=2)

    def drag(
        self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.0
    ) -> bool:
        """Drag from start to end position."""
        return self.mouse_drag(start_x, start_y, end_x, end_y, duration=duration)

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse to position (alias for mouse_move)."""
        return self.mouse_move(x, y, duration)

    def scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> bool:
        """Scroll mouse wheel (alias for mouse_scroll)."""
        return self.mouse_scroll(clicks, x, y)

    # Keyboard operations

    def key_press(self, key: str | Key, presses: int = 1, interval: float = 0.0) -> bool:
        """Press key (down and up)."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        key_str = key.value if isinstance(key, Key) else key
        self._record_action("key_press", key=key_str, presses=presses, interval=interval)
        return True

    def key_down(self, key: str | Key) -> bool:
        """Press and hold key."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        key_str = key.value if isinstance(key, Key) else key
        self._pressed_keys.add(key_str)
        self._record_action("key_down", key=key_str)
        return True

    def key_up(self, key: str | Key) -> bool:
        """Release key."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        key_str = key.value if isinstance(key, Key) else key
        self._pressed_keys.discard(key_str)
        self._record_action("key_up", key=key_str)
        return True

    def type_text(self, text: str, interval: float = 0.0) -> bool:
        """Type text string."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        self._record_action("type_text", text=text, interval=interval)
        return True

    def hotkey(self, *keys: str | Key) -> bool:
        """Press key combination."""
        self._simulate_latency()
        if not self._check_failure():
            return False

        key_strs = [k.value if isinstance(k, Key) else k for k in keys]
        self._record_action("hotkey", keys=key_strs)
        return True

    def is_key_pressed(self, key: str | Key) -> bool:
        """Check if key is currently pressed."""
        key_str = key.value if isinstance(key, Key) else key
        return key_str in self._pressed_keys

    # Test helper methods

    def get_typed_text(self) -> list[str]:
        """Get all text that was typed.

        Returns:
            List of all text strings that were typed
        """
        return [
            action.params["text"] for action in self.actions if action.action_type == "type_text"
        ]

    def get_clicks(self) -> list[dict[str, Any]]:
        """Get all mouse clicks.

        Returns:
            List of click action parameters
        """
        return [action.params for action in self.actions if action.action_type == "mouse_click"]

    def assert_clicked_at(self, x: int, y: int, button: str = "left") -> None:
        """Assert that a click occurred at coordinates.

        Args:
            x: Expected X coordinate
            y: Expected Y coordinate
            button: Expected mouse button

        Raises:
            AssertionError: If no matching click was found
        """
        clicks = self.get_clicks()
        for click in clicks:
            if click["x"] == x and click["y"] == y and click["button"] == button:
                return
        raise AssertionError(
            f"No {button} click at ({x}, {y}). Found clicks at: "
            f"{[(c['x'], c['y'], c['button']) for c in clicks]}"
        )

    def assert_typed_text(self, text: str) -> None:
        """Assert that specific text was typed.

        Args:
            text: Expected text

        Raises:
            AssertionError: If text was not typed
        """
        typed = self.get_typed_text()
        if text not in typed:
            raise AssertionError(f"Text '{text}' not typed. Typed text: {typed}")

    def assert_key_pressed(self, key: str) -> None:
        """Assert that specific key was pressed.

        Args:
            key: Expected key

        Raises:
            AssertionError: If key was not pressed
        """
        key_presses = [
            action.params["key"]
            for action in self.actions
            if action.action_type in ("key_press", "key_down")
        ]
        if key not in key_presses:
            raise AssertionError(f"Key '{key}' not pressed. Pressed keys: {key_presses}")

    def assert_hotkey_pressed(self, *keys: str) -> None:
        """Assert that specific hotkey combination was pressed.

        Args:
            *keys: Expected key combination

        Raises:
            AssertionError: If hotkey was not pressed
        """
        hotkeys = [
            tuple(action.params["keys"])
            for action in self.actions
            if action.action_type == "hotkey"
        ]
        key_tuple = tuple(keys)
        if key_tuple not in hotkeys:
            raise AssertionError(f"Hotkey {key_tuple} not pressed. Pressed hotkeys: {hotkeys}")

    def get_actions_by_type(self, action_type: str) -> list[InputAction]:
        """Get all actions of a specific type.

        Args:
            action_type: Type of action to filter

        Returns:
            List of matching actions
        """
        return [action for action in self.actions if action.action_type == action_type]

    def reset(self) -> None:
        """Clear all recorded actions and reset state."""
        self.actions.clear()
        self._call_count = 0
        self._mouse_position = MousePosition(x=0, y=0)
        self._pressed_keys.clear()

    def get_action_count(self) -> int:
        """Get total number of recorded actions."""
        return len(self.actions)

    def get_last_action(self) -> InputAction | None:
        """Get the most recent action."""
        return self.actions[-1] if self.actions else None
