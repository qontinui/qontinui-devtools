"""Mock implementation of IScreenCapture for testing.

This module provides a mock screen capture that returns configurable test images
instead of actual screen captures. Useful for testing visual workflows without
requiring a display.
"""

import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from PIL.ImageFont import ImageFont as DefaultImageFont
from qontinui.hal.interfaces import IScreenCapture
from qontinui.hal.interfaces.screen_capture import Monitor


class MockScreenCapture(IScreenCapture):
    """Mock implementation of IScreenCapture.

    This mock returns configurable test images instead of capturing the screen.
    Allows testing of screen-dependent workflows without a real display.

    Attributes:
        default_image: Image to return from captures
        latency: Simulated capture latency in seconds
        capture_count: Number of captures performed
        monitors: List of mock monitor configurations

    Example:
        >>> capture = MockScreenCapture()
        >>> img = capture.capture_screen()
        >>> assert img.size == (1920, 1080)
        >>> assert capture.capture_count == 1
    """

    def __init__(
        self,
        default_image: Image.Image | None = None,
        latency: float = 0.0,
        monitors: list[Monitor] | None = None,
    ) -> None:
        """Initialize mock screen capture.

        Args:
            default_image: Image to return (creates test image if None)
            latency: Simulated capture latency in seconds
            monitors: List of monitor configurations (creates default if None)
        """
        self.default_image = default_image or self._create_test_image()
        self.latency = latency
        self.capture_count = 0
        self._captured_regions: list[tuple[int, int, int, int]] = []
        self._saved_screenshots: list[str] = []

        # Set up default monitors if not provided
        if monitors is None:
            self.monitors = [
                Monitor(
                    index=0,
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                    scale=1.0,
                    is_primary=True,
                    name="Primary Monitor",
                )
            ]
        else:
            self.monitors = monitors

    def _simulate_latency(self) -> None:
        """Simulate capture latency."""
        if self.latency > 0:
            time.sleep(self.latency)

    def capture_screen(self, monitor: int | None = None) -> Image.Image:
        """Capture entire screen or specific monitor.

        Args:
            monitor: Monitor index (0-based), None for primary

        Returns:
            PIL Image of screenshot
        """
        self._simulate_latency()
        self.capture_count += 1

        if monitor is not None and monitor < len(self.monitors):
            mon = self.monitors[monitor]
            return self.default_image.resize((mon.width, mon.height))

        return self.default_image.copy()

    def capture_region(
        self, x: int, y: int, width: int, height: int, monitor: int | None = None
    ) -> Image.Image:
        """Capture specific region.

        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Region width in pixels
            height: Region height in pixels
            monitor: Optional monitor index

        Returns:
            PIL Image of region
        """
        self._simulate_latency()
        self.capture_count += 1
        self._captured_regions.append((x, y, width, height))

        # Ensure coordinates are within image bounds
        img_width, img_height = self.default_image.size
        x = max(0, min(x, img_width))
        y = max(0, min(y, img_height))
        width = min(width, img_width - x)
        height = min(height, img_height - y)

        return self.default_image.crop((x, y, x + width, y + height))

    def get_monitors(self) -> list[Monitor]:
        """Get list of available monitors.

        Returns:
            List of Monitor objects
        """
        return self.monitors.copy()

    def get_primary_monitor(self) -> Monitor:
        """Get primary monitor.

        Returns:
            Primary Monitor object
        """
        for monitor in self.monitors:
            if monitor.is_primary:
                return monitor
        return self.monitors[0]

    def get_screen_size(self) -> tuple[int, int]:
        """Get screen size.

        Returns:
            Tuple of (width, height) in pixels
        """
        primary = self.get_primary_monitor()
        return (primary.width, primary.height)

    def get_pixel_color(self, x: int, y: int, monitor: int | None = None) -> tuple[int, int, int]:
        """Get color of pixel at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            monitor: Optional monitor index

        Returns:
            RGB color tuple
        """
        self._simulate_latency()

        # Ensure coordinates are within bounds
        width, height = self.default_image.size
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))

        pixel = self.default_image.getpixel((x, y))
        if isinstance(pixel, int):
            # Grayscale image
            return (pixel, pixel, pixel)
        elif isinstance(pixel, tuple) and len(pixel) == 4:
            # RGBA image
            return (pixel[0], pixel[1], pixel[2])
        else:
            # RGB image
            return pixel  # type: ignore

    def save_screenshot(
        self,
        filepath: str,
        monitor: int | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> str:
        """Save screenshot to file.

        Args:
            filepath: Path to save screenshot
            monitor: Optional monitor to capture
            region: Optional region (x, y, width, height)

        Returns:
            Path where screenshot was saved
        """
        self._simulate_latency()

        if region is not None:
            x, y, width, height = region
            img = self.capture_region(x, y, width, height, monitor)
        else:
            img = self.capture_screen(monitor)

        # Create parent directory if it doesn't exist
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save the image
        img.save(filepath)
        self._saved_screenshots.append(filepath)

        return filepath

    # Test helper methods

    def set_test_image(self, image: Image.Image) -> None:
        """Set image to return from captures.

        Args:
            image: PIL Image to use as test image
        """
        self.default_image = image

    def load_test_image(self, path: str) -> None:
        """Load test image from file.

        Args:
            path: Path to image file
        """
        self.default_image = Image.open(path)

    def add_monitor(self, monitor: Monitor) -> None:
        """Add a monitor to the mock configuration.

        Args:
            monitor: Monitor to add
        """
        self.monitors.append(monitor)

    def set_monitors(self, monitors: list[Monitor]) -> None:
        """Set the list of monitors.

        Args:
            monitors: List of monitors
        """
        self.monitors = monitors

    def get_captured_regions(self) -> list[tuple[int, int, int, int]]:
        """Get list of all captured regions.

        Returns:
            List of (x, y, width, height) tuples
        """
        return self._captured_regions.copy()

    def get_saved_screenshots(self) -> list[str]:
        """Get list of saved screenshot paths.

        Returns:
            List of file paths
        """
        return self._saved_screenshots.copy()

    def reset(self) -> None:
        """Clear capture history and reset state."""
        self.capture_count = 0
        self._captured_regions.clear()
        self._saved_screenshots.clear()

    @staticmethod
    def _create_test_image(
        width: int = 1920,
        height: int = 1080,
        background_color: str = "white",
        add_markers: bool = True,
    ) -> Image.Image:
        """Create a simple test image.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            background_color: Background color name or hex
            add_markers: Whether to add visual markers

        Returns:
            PIL Image object
        """
        img = Image.new("RGB", (width, height), color=background_color)

        if add_markers:
            draw = ImageDraw.Draw(img)

            # Add text marker
            try:
                # Try to use a truetype font
                font: FreeTypeFont | DefaultImageFont = ImageFont.truetype("arial.ttf", 36)
            except OSError:
                # Fall back to default font
                font = ImageFont.load_default()

            text = "Test Image"
            draw.text((100, 100), text, fill="black", font=font)

            # Add corner markers
            marker_size = 50
            draw.rectangle([0, 0, marker_size, marker_size], fill="red")  # Top-left
            draw.rectangle([width - marker_size, 0, width, marker_size], fill="green")  # Top-right
            draw.rectangle(
                [0, height - marker_size, marker_size, height], fill="blue"
            )  # Bottom-left
            draw.rectangle(
                [width - marker_size, height - marker_size, width, height], fill="yellow"
            )  # Bottom-right

            # Add center crosshair
            center_x, center_y = width // 2, height // 2
            crosshair_size = 20
            draw.line(
                [(center_x - crosshair_size, center_y), (center_x + crosshair_size, center_y)],
                fill="black",
                width=2,
            )
            draw.line(
                [(center_x, center_y - crosshair_size), (center_x, center_y + crosshair_size)],
                fill="black",
                width=2,
            )

        return img

    @staticmethod
    def create_test_image_with_text(
        text: str,
        width: int = 800,
        height: int = 600,
        text_position: tuple[int, int] = (100, 100),
        text_size: int = 36,
        text_color: str = "black",
        background_color: str = "white",
    ) -> Image.Image:
        """Create a test image with custom text.

        Args:
            text: Text to display
            width: Image width
            height: Image height
            text_position: (x, y) position for text
            text_size: Font size
            text_color: Text color
            background_color: Background color

        Returns:
            PIL Image with text
        """
        img = Image.new("RGB", (width, height), color=background_color)
        draw = ImageDraw.Draw(img)

        try:
            font: FreeTypeFont | DefaultImageFont = ImageFont.truetype("arial.ttf", text_size)
        except OSError:
            font = ImageFont.load_default()

        draw.text(text_position, text, fill=text_color, font=font)
        return img

    @staticmethod
    def create_test_pattern(
        width: int = 800, height: int = 600, pattern_type: str = "checkerboard"
    ) -> Image.Image:
        """Create a test pattern image.

        Args:
            width: Image width
            height: Image height
            pattern_type: Type of pattern ("checkerboard", "gradient", "grid")

        Returns:
            PIL Image with pattern
        """
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        if pattern_type == "checkerboard":
            square_size = 50
            for i in range(0, width, square_size):
                for j in range(0, height, square_size):
                    if (i // square_size + j // square_size) % 2 == 0:
                        draw.rectangle([i, j, i + square_size, j + square_size], fill="black")

        elif pattern_type == "gradient":
            for i in range(width):
                color_value = int(255 * i / width)
                draw.line([(i, 0), (i, height)], fill=(color_value, color_value, color_value))

        elif pattern_type == "grid":
            grid_size = 50
            for i in range(0, width, grid_size):
                draw.line([(i, 0), (i, height)], fill="gray", width=1)
            for j in range(0, height, grid_size):
                draw.line([(0, j), (width, j)], fill="gray", width=1)

        return img
