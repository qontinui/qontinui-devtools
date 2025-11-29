"""Mock implementation of IPatternMatcher for testing.

This module provides a mock pattern matcher with configurable behavior,
allowing tests to simulate pattern matching without actual image processing.
"""

import hashlib
import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image
from qontinui.hal.interfaces import IPatternMatcher
from qontinui.hal.interfaces.pattern_matcher import Feature, Match


@dataclass
class MatchConfig:
    """Configuration for a mock pattern match.

    Attributes:
        template_id: Identifier for the template
        success: Whether match should succeed
        location: Location to return (x, y)
        confidence: Confidence score to return
        width: Width of matched region
        height: Height of matched region
    """

    template_id: str
    success: bool
    location: tuple[int, int] | None
    confidence: float
    width: int = 100
    height: int = 100


class MockPatternMatcher(IPatternMatcher):
    """Mock implementation of IPatternMatcher.

    This mock allows configuration of pattern matching behavior for testing.
    Can simulate successful matches, failures, and various confidence levels.

    Attributes:
        default_success_rate: Probability of match success (0.0-1.0)
        default_location: Default location for successful matches
        latency: Simulated matching latency in seconds
        match_attempts: List of all match attempts

    Example:
        >>> matcher = MockPatternMatcher()
        >>> matcher.configure_match("button", success=True, location=(100, 200))
        >>> result = matcher.find_pattern(screenshot, template)
        >>> assert result is not None
        >>> assert result.center == (100, 200)
    """

    def __init__(
        self,
        default_success_rate: float = 1.0,
        default_location: tuple[int, int] = (100, 100),
        latency: float = 0.0,
    ) -> None:
        """Initialize mock pattern matcher.

        Args:
            default_success_rate: Probability of match success (0.0-1.0)
            default_location: Default (x, y) location for matches
            latency: Simulated matching latency in seconds
        """
        self.default_success_rate = default_success_rate
        self.default_location = default_location
        self.latency = latency
        self._match_configs: dict[str, MatchConfig] = {}
        self.match_attempts: list[dict[str, Any]] = []

    def _simulate_latency(self) -> None:
        """Simulate matching latency."""
        if self.latency > 0:
            time.sleep(self.latency)

    def _hash_image(self, image: Image.Image) -> str:
        """Create hash of image for identification.

        Args:
            image: PIL Image

        Returns:
            Hash string
        """
        return hashlib.md5(image.tobytes()).hexdigest()

    def _record_attempt(self, attempt_type: str, **kwargs: Any) -> None:
        """Record a match attempt."""
        self.match_attempts.append({"type": attempt_type, "timestamp": time.time(), **kwargs})

    def _get_config(self, template: Image.Image) -> MatchConfig | None:
        """Get configuration for template.

        Args:
            template: Template image

        Returns:
            MatchConfig if configured, None otherwise
        """
        template_hash = self._hash_image(template)

        # Check for hash-based config
        if template_hash in self._match_configs:
            return self._match_configs[template_hash]

        # Check for default config
        if "default" in self._match_configs:
            return self._match_configs["default"]

        return None

    def find_pattern(
        self,
        haystack: Image.Image,
        needle: Image.Image,
        confidence: float = 0.9,
        grayscale: bool = False,
    ) -> Match | None:
        """Find single pattern occurrence in image.

        Args:
            haystack: Image to search in
            needle: Pattern to search for
            confidence: Minimum confidence threshold
            grayscale: Convert to grayscale before matching

        Returns:
            Match object if found, None otherwise
        """
        self._simulate_latency()
        self._record_attempt(
            "find_pattern",
            haystack_size=haystack.size,
            needle_size=needle.size,
            confidence=confidence,
            grayscale=grayscale,
        )

        # Check for configured behavior
        config = self._get_config(needle)
        if config is not None:
            if not config.success or config.location is None:
                return None

            x, y = config.location
            return Match(
                x=x,
                y=y,
                width=config.width,
                height=config.height,
                confidence=config.confidence,
                center=(x + config.width // 2, y + config.height // 2),
            )

        # Default behavior
        if random.random() < self.default_success_rate:
            x, y = self.default_location
            w, h = needle.size
            return Match(
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=confidence + 0.05,
                center=(x + w // 2, y + h // 2),
            )

        return None

    def find_all_patterns(
        self,
        haystack: Image.Image,
        needle: Image.Image,
        confidence: float = 0.9,
        grayscale: bool = False,
        limit: int | None = None,
    ) -> list[Match]:
        """Find all pattern occurrences in image.

        Args:
            haystack: Image to search in
            needle: Pattern to search for
            confidence: Minimum confidence threshold
            grayscale: Convert to grayscale before matching
            limit: Maximum number of matches to return

        Returns:
            List of Match objects
        """
        self._simulate_latency()
        self._record_attempt(
            "find_all_patterns",
            haystack_size=haystack.size,
            needle_size=needle.size,
            confidence=confidence,
            limit=limit,
        )

        # Check for configured behavior
        config = self._get_config(needle)
        if config is not None:
            if not config.success or config.location is None:
                return []

            # Return single match for configured behavior
            x, y = config.location
            match = Match(
                x=x,
                y=y,
                width=config.width,
                height=config.height,
                confidence=config.confidence,
                center=(x + config.width // 2, y + config.height // 2),
            )
            return [match]

        # Default behavior - return 0-3 matches
        num_matches = random.randint(0, 3) if random.random() < self.default_success_rate else 0
        if limit is not None:
            num_matches = min(num_matches, limit)

        matches = []
        w, h = needle.size
        for i in range(num_matches):
            x = self.default_location[0] + i * 50
            y = self.default_location[1] + i * 50
            matches.append(
                Match(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=confidence + random.uniform(0.0, 0.1),
                    center=(x + w // 2, y + h // 2),
                )
            )

        return matches

    def find_features(self, image: Image.Image, method: str = "orb") -> list[Feature]:
        """Detect features in image.

        Args:
            image: Image to analyze
            method: Feature detection method

        Returns:
            List of detected features
        """
        self._simulate_latency()
        self._record_attempt("find_features", image_size=image.size, method=method)

        # Return mock features
        num_features = random.randint(10, 50)
        features = []
        width, height = image.size

        for _i in range(num_features):
            features.append(
                Feature(
                    x=random.uniform(0, width),
                    y=random.uniform(0, height),
                    size=random.uniform(5, 20),
                    angle=random.uniform(0, 360),
                    response=random.uniform(0.5, 1.0),
                    octave=random.randint(0, 3),
                    descriptor=np.random.rand(32) if method == "orb" else None,
                )
            )

        return features

    def match_features(
        self, features1: list[Feature], features2: list[Feature], threshold: float = 0.7
    ) -> list[tuple[Feature, Feature]]:
        """Match features between two feature sets.

        Args:
            features1: First feature set
            features2: Second feature set
            threshold: Matching threshold

        Returns:
            List of matched feature pairs
        """
        self._simulate_latency()
        self._record_attempt(
            "match_features",
            num_features1=len(features1),
            num_features2=len(features2),
            threshold=threshold,
        )

        # Return random matches
        num_matches = min(len(features1), len(features2)) // 2
        matches = []

        indices1 = random.sample(range(len(features1)), min(num_matches, len(features1)))
        indices2 = random.sample(range(len(features2)), min(num_matches, len(features2)))

        for i1, i2 in zip(indices1, indices2, strict=False):
            matches.append((features1[i1], features2[i2]))

        return matches

    def find_template_multiscale(
        self,
        haystack: Image.Image,
        needle: Image.Image,
        scales: list[float] | None = None,
        confidence: float = 0.9,
    ) -> Match | None:
        """Find pattern at multiple scales.

        Args:
            haystack: Image to search in
            needle: Pattern to search for
            scales: List of scales to try
            confidence: Minimum confidence threshold

        Returns:
            Best Match if found, None otherwise
        """
        self._simulate_latency()
        scales = scales or [0.5, 0.75, 1.0, 1.25, 1.5]
        self._record_attempt(
            "find_template_multiscale",
            haystack_size=haystack.size,
            needle_size=needle.size,
            scales=scales,
            confidence=confidence,
        )

        # Just use regular find_pattern
        return self.find_pattern(haystack, needle, confidence)

    def compare_histograms(
        self, image1: Image.Image, image2: Image.Image, method: str = "correlation"
    ) -> float:
        """Compare histograms of two images.

        Args:
            image1: First image
            image2: Second image
            method: Comparison method

        Returns:
            Similarity score (0.0 to 1.0)
        """
        self._simulate_latency()
        self._record_attempt(
            "compare_histograms", image1_size=image1.size, image2_size=image2.size, method=method
        )

        # Return random similarity score
        return random.uniform(0.5, 1.0)

    def detect_edges(
        self, image: Image.Image, low_threshold: int = 50, high_threshold: int = 150
    ) -> Image.Image:
        """Detect edges in image.

        Args:
            image: Input image
            low_threshold: Low threshold for edge detection
            high_threshold: High threshold for edge detection

        Returns:
            Edge-detected image (mock - returns grayscale version)
        """
        self._simulate_latency()
        self._record_attempt(
            "detect_edges",
            image_size=image.size,
            low_threshold=low_threshold,
            high_threshold=high_threshold,
        )

        # Return grayscale version as mock edge detection
        return image.convert("L")

    # Test helper methods

    def configure_match(
        self,
        template_id: str,
        success: bool,
        location: tuple[int, int] | None = None,
        confidence: float = 0.95,
        width: int = 100,
        height: int = 100,
    ) -> None:
        """Configure behavior for specific template.

        Args:
            template_id: Identifier for template ("default" for default behavior)
            success: Whether match should succeed
            location: Location to return (x, y) if success=True
            confidence: Confidence score to return
            width: Width of matched region
            height: Height of matched region
        """
        self._match_configs[template_id] = MatchConfig(
            template_id=template_id,
            success=success,
            location=location,
            confidence=confidence,
            width=width,
            height=height,
        )

    def configure_match_for_image(
        self,
        template: Image.Image,
        success: bool,
        location: tuple[int, int] | None = None,
        confidence: float = 0.95,
    ) -> None:
        """Configure behavior for specific template image.

        Args:
            template: Template image
            success: Whether match should succeed
            location: Location to return if success=True
            confidence: Confidence score to return
        """
        template_hash = self._hash_image(template)
        w, h = template.size
        self.configure_match(
            template_hash,
            success=success,
            location=location,
            confidence=confidence,
            width=w,
            height=h,
        )

    def get_match_attempts(self, attempt_type: str | None = None) -> list[dict[str, Any]]:
        """Get list of match attempts.

        Args:
            attempt_type: Filter by attempt type (None for all)

        Returns:
            List of attempt records
        """
        if attempt_type is None:
            return self.match_attempts.copy()
        return [a for a in self.match_attempts if a["type"] == attempt_type]

    def reset(self) -> None:
        """Clear match attempts and reset state."""
        self.match_attempts.clear()

    def clear_configs(self) -> None:
        """Clear all match configurations."""
        self._match_configs.clear()
