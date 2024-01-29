"""Various utility functions."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any


class IdentifierGenerator:
    """Generator for unique identifiers."""

    def __init__(self) -> None:
        """Init."""
        self._num_gen = self._number_generator()

    def __call__(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self._num_gen))

    @staticmethod
    def _number_generator() -> Generator[int, Any, None]:
        i = 1
        while True:
            yield i
            i += 1
