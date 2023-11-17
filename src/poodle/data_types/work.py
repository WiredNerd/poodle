"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ..reporters.basic import report_not_found, report_summary
from .data import PoodleConfig
from .interfaces import Mutator

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class PoodleWork:
    """Work-in-progress data gathered into single structure for easy passing between functions."""

    def __init__(self, config: PoodleConfig) -> None:
        """Init from PoodleConfig."""
        self.config = config
        self.folder_zips: dict[Path, Path] = {}
        self.mutators: list[Mutator | Callable] = []
        self.runner: Callable | None = None
        self.reporters: list[Callable] = []

        def number_generator() -> Generator[int, Any, None]:
            i = 1
            while True:
                yield i
                i += 1

        self._num_gen = number_generator()

    def next_num(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self._num_gen))
