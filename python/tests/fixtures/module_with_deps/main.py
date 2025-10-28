"""Main module that imports others."""

from .helper import HelperClass
from .utils import utility_function


class MainClass:
    """Main class that uses helpers."""

    def __init__(self):
        self.helper = HelperClass()

    def do_work(self):
        """Perform work using utilities."""
        result = utility_function()
        self.helper.assist()
        return result
