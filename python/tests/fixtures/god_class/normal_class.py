"""Example well-designed class with single responsibility for testing."""


class NormalClass:
    """Well-designed class with single responsibility (counter)."""

    def __init__(self) -> None:
        """Initialize counter."""
        self.value = 0

    def increment(self) -> None:
        """Increment counter by 1."""
        self.value += 1

    def decrement(self) -> None:
        """Decrement counter by 1."""
        self.value -= 1

    def get_value(self) -> int:
        """Get current value."""
        return self.value

    def reset(self) -> None:
        """Reset counter to zero."""
        self.value = 0


class WellDesignedValidator:
    """Example of focused validation class."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.errors = []

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        return "@" in email and "." in email

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        return len(phone) >= 10

    def validate_age(self, age: int) -> bool:
        """Validate age is within range."""
        return 0 <= age <= 150

    def get_errors(self) -> list[str]:
        """Get validation errors."""
        return self.errors
