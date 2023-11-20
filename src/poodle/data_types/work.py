"""Shared Data Classes used by Poodle."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import click

from .. import PoodleTrialRunError
from .data import PoodleConfig
from .interfaces import Mutator

logger = logging.getLogger(__name__)

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
        self.runner: Callable = lambda *_, **__: None
        self.reporters: list[Callable] = []

        self.echo = click.echo if config.echo_enabled else lambda *_, **__: None

        def number_generator() -> Generator[int, Any, None]:
            i = 1
            while True:
                yield i
                i += 1

        self._num_gen = number_generator()

    def next_num(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self._num_gen))
