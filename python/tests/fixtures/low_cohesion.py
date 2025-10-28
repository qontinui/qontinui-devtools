"""Test fixture: Class with low cohesion (methods don't share attributes)."""


class LowCohesionClass:
    """A class where methods don't share attributes (poor cohesion)."""

    def method_a(self):
        """Uses only attr_a."""
        self.attr_a = 1
        return self.attr_a * 2

    def method_b(self):
        """Uses only attr_b."""
        self.attr_b = 2
        return self.attr_b + 5

    def method_c(self):
        """Uses only attr_c."""
        self.attr_c = 3
        return self.attr_c - 1

    def method_d(self):
        """Uses only attr_d."""
        self.attr_d = 4
        return self.attr_d / 2

    def method_e(self):
        """Uses only attr_e."""
        self.attr_e = 5
        return self.attr_e ** 2


class HighCohesionClass:
    """A class where methods share attributes (good cohesion)."""

    def __init__(self):
        self.data = []
        self.count = 0

    def add_item(self, item):
        """Uses data and count."""
        self.data.append(item)
        self.count += 1

    def remove_item(self, item):
        """Uses data and count."""
        if item in self.data:
            self.data.remove(item)
            self.count -= 1

    def get_total(self):
        """Uses count."""
        return self.count

    def get_items(self):
        """Uses data."""
        return list(self.data)

    def clear(self):
        """Uses data and count."""
        self.data.clear()
        self.count = 0


class MediumCohesionClass:
    """A class with moderate cohesion (some groups of related methods)."""

    def __init__(self):
        self.name = ""
        self.age = 0
        self.address = ""
        self.phone = ""

    def set_name(self, name):
        """Uses name."""
        self.name = name

    def get_name(self):
        """Uses name."""
        return self.name

    def set_age(self, age):
        """Uses age."""
        self.age = age

    def get_age(self):
        """Uses age."""
        return self.age

    def set_contact(self, address, phone):
        """Uses address and phone."""
        self.address = address
        self.phone = phone

    def get_contact(self):
        """Uses address and phone."""
        return f"{self.address}, {self.phone}"
