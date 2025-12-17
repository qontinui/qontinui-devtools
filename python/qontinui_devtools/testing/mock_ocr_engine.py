"""Mock implementation of IOCREngine for testing.

This module provides a mock OCR engine with configurable text extraction,
allowing tests to simulate OCR without actual text recognition processing.
"""

import hashlib
import random
import time
from typing import Any

from PIL import Image
from qontinui.hal.interfaces import IOCREngine, TextMatch, TextRegion


class MockOCREngine(IOCREngine):
    """Mock implementation of IOCREngine.

    This mock allows configuration of OCR behavior for testing. Can return
    predefined text for specific images or simulate OCR accuracy issues.

    Attributes:
        default_text: Default text to return
        accuracy: Simulated OCR accuracy (0.0-1.0)
        latency: Simulated OCR latency in seconds
        ocr_calls: List of all OCR calls made

    Example:
        >>> ocr = MockOCREngine(default_text="Login")
        >>> text = ocr.extract_text(screenshot)
        >>> assert text == "Login"
    """

    def __init__(
        self,
        default_text: str = "Mock OCR Text",
        accuracy: float = 1.0,
        latency: float = 0.0,
        supported_languages: list[str] | None = None,
    ) -> None:
        """Initialize mock OCR engine.

        Args:
            default_text: Default text to return for extractions
            accuracy: Simulated accuracy (1.0 = perfect, <1.0 = add noise)
            latency: Simulated OCR latency in seconds
            supported_languages: List of supported language codes
        """
        self.default_text = default_text
        self.accuracy = accuracy
        self.latency = latency
        self._text_map: dict[str, str] = {}  # image hash → text
        self._region_map: dict[str, list[TextRegion]] = {}  # image hash → regions
        self.ocr_calls: list[dict[str, Any]] = []
        self._supported_languages = supported_languages or ["en", "es", "fr", "de", "zh"]

    def _simulate_latency(self) -> None:
        """Simulate OCR processing latency."""
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

    def _record_call(self, call_type: str, **kwargs: Any) -> None:
        """Record an OCR call."""
        self.ocr_calls.append({"type": call_type, "timestamp": time.time(), **kwargs})

    def _add_noise(self, text: str) -> str:
        """Add OCR errors based on accuracy.

        Args:
            text: Original text

        Returns:
            Text with simulated OCR errors
        """
        if self.accuracy >= 1.0:
            return text

        chars = list(text)
        for i in range(len(chars)):
            if random.random() > self.accuracy:
                if chars[i].isalpha():
                    # Replace with similar-looking character
                    if chars[i].isupper():
                        chars[i] = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                    else:
                        chars[i] = random.choice("abcdefghijklmnopqrstuvwxyz")
                elif chars[i].isdigit():
                    chars[i] = random.choice("0123456789")

        return "".join(chars)

    def extract_text(self, image: Image.Image, languages: list[str] | None = None) -> str:
        """Extract all text from image.

        Args:
            image: Image to extract text from
            languages: List of language codes

        Returns:
            Extracted text as string
        """
        self._simulate_latency()
        self._record_call("extract_text", image_size=image.size, languages=languages)

        # Check if configured for this image
        img_hash = self._hash_image(image)
        if img_hash in self._text_map:
            return self._add_noise(self._text_map[img_hash])

        return self._add_noise(self.default_text)

    def get_text_regions(
        self, image: Image.Image, languages: list[str] | None = None, min_confidence: float = 0.5
    ) -> list[TextRegion]:
        """Get all text regions with bounding boxes.

        Args:
            image: Image to analyze
            languages: List of language codes
            min_confidence: Minimum confidence threshold

        Returns:
            List of TextRegion objects
        """
        self._simulate_latency()
        self._record_call(
            "get_text_regions",
            image_size=image.size,
            languages=languages,
            min_confidence=min_confidence,
        )

        # Check if configured for this image
        img_hash = self._hash_image(image)
        if img_hash in self._region_map:
            # Filter by confidence
            regions = self._region_map[img_hash]
            return [r for r in regions if r.confidence >= min_confidence]

        # Return default single region
        text = self.extract_text(image, languages)
        width, height = image.size
        return [
            TextRegion(
                text=text,
                x=10,
                y=10,
                width=min(len(text) * 10, width - 20),
                height=30,
                confidence=self.accuracy,
                language=languages[0] if languages else "en",
            )
        ]

    def find_text(
        self, image: Image.Image, text: str, case_sensitive: bool = False, confidence: float = 0.8
    ) -> TextMatch | None:
        """Find specific text in image.

        Args:
            image: Image to search
            text: Text to find
            case_sensitive: Whether search is case-sensitive
            confidence: Minimum confidence threshold

        Returns:
            TextMatch if found, None otherwise
        """
        self._simulate_latency()
        self._record_call(
            "find_text",
            image_size=image.size,
            text=text,
            case_sensitive=case_sensitive,
            confidence=confidence,
        )

        # Get all regions
        regions = self.get_text_regions(image, min_confidence=confidence)

        # Search for text
        for region in regions:
            region_text = region.text if case_sensitive else region.text.lower()
            search_text = text if case_sensitive else text.lower()

            if search_text in region_text:
                similarity = 1.0 if region_text == search_text else 0.9
                return TextMatch(text=region.text, region=region, similarity=similarity)

        return None

    def find_all_text(
        self, image: Image.Image, text: str, case_sensitive: bool = False, confidence: float = 0.8
    ) -> list[TextMatch]:
        """Find all occurrences of text in image.

        Args:
            image: Image to search
            text: Text to find
            case_sensitive: Whether search is case-sensitive
            confidence: Minimum confidence threshold

        Returns:
            List of TextMatch objects
        """
        self._simulate_latency()
        self._record_call(
            "find_all_text",
            image_size=image.size,
            text=text,
            case_sensitive=case_sensitive,
            confidence=confidence,
        )

        # Get all regions
        regions = self.get_text_regions(image, min_confidence=confidence)

        # Search for text in all regions
        matches: list[Any] = []
        for region in regions:
            region_text = region.text if case_sensitive else region.text.lower()
            search_text = text if case_sensitive else text.lower()

            if search_text in region_text:
                similarity = 1.0 if region_text == search_text else 0.9
                matches.append(TextMatch(text=region.text, region=region, similarity=similarity))

        return matches

    def extract_text_from_region(
        self,
        image: Image.Image,
        region: tuple[int, int, int, int],
        languages: list[str] | None = None,
    ) -> str:
        """Extract text from specific region.

        Args:
            image: Image containing text
            region: Region bounds (x, y, width, height)
            languages: List of language codes

        Returns:
            Extracted text from region
        """
        self._simulate_latency()
        self._record_call(
            "extract_text_from_region", image_size=image.size, region=region, languages=languages
        )

        # Crop image to region
        x, y, width, height = region
        cropped = image.crop((x, y, x + width, y + height))

        # Extract text from cropped image
        return self.extract_text(cropped, languages)

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes.

        Returns:
            List of language codes
        """
        return self._supported_languages.copy()

    def preprocess_image(
        self,
        image: Image.Image,
        grayscale: bool = True,
        denoise: bool = True,
        threshold: bool = False,
    ) -> Image.Image:
        """Preprocess image for better OCR results.

        Args:
            image: Input image
            grayscale: Convert to grayscale
            denoise: Apply denoising
            threshold: Apply thresholding

        Returns:
            Preprocessed image (mock - applies basic transformations)
        """
        self._simulate_latency()
        self._record_call(
            "preprocess_image",
            image_size=image.size,
            grayscale=grayscale,
            denoise=denoise,
            threshold=threshold,
        )

        result = image.copy()

        if grayscale:
            result = result.convert("L")

        if threshold:
            # Simple threshold
            result = result.point(lambda x: 0 if x < 128 else 255)

        return result

    def detect_text_orientation(self, image: Image.Image) -> dict[str, Any]:
        """Detect text orientation in image.

        Args:
            image: Image to analyze

        Returns:
            Dictionary with orientation info
        """
        self._simulate_latency()
        self._record_call("detect_text_orientation", image_size=image.size)

        # Return mock orientation data
        return {
            "angle": random.choice([0, 90, 180, 270]),
            "confidence": self.accuracy,
            "script": "Latin",
        }

    # Test helper methods

    def configure_text(self, image: Image.Image, text: str) -> None:
        """Configure text to return for specific image.

        Args:
            image: Image to configure
            text: Text to return when this image is processed
        """
        img_hash = self._hash_image(image)
        self._text_map[img_hash] = text

    def configure_regions(self, image: Image.Image, regions: list[TextRegion]) -> None:
        """Configure text regions for specific image.

        Args:
            image: Image to configure
            regions: List of text regions to return
        """
        img_hash = self._hash_image(image)
        self._region_map[img_hash] = regions

    def configure_text_by_hash(self, image_hash: str, text: str) -> None:
        """Configure text by image hash.

        Args:
            image_hash: Hash of image
            text: Text to return
        """
        self._text_map[image_hash] = text

    def get_ocr_calls(self, call_type: str | None = None) -> list[dict[str, Any]]:
        """Get list of OCR calls.

        Args:
            call_type: Filter by call type (None for all)

        Returns:
            List of call records
        """
        if call_type is None:
            return self.ocr_calls.copy()
        return [call for call in self.ocr_calls if call["type"] == call_type]

    def set_accuracy(self, accuracy: float) -> None:
        """Set OCR accuracy for subsequent calls.

        Args:
            accuracy: New accuracy value (0.0-1.0)
        """
        self.accuracy = max(0.0, min(1.0, accuracy))

    def add_supported_language(self, language: str) -> None:
        """Add a supported language.

        Args:
            language: Language code to add
        """
        if language not in self._supported_languages:
            self._supported_languages.append(language)

    def reset(self) -> None:
        """Clear OCR call history and reset state."""
        self.ocr_calls.clear()

    def clear_configs(self) -> None:
        """Clear all text and region configurations."""
        self._text_map.clear()
        self._region_map.clear()
