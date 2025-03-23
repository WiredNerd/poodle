"""Containers for Work-in-progress data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import IO, TYPE_CHECKING, Any, AnyStr, Callable

import click

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from .data import PoodleConfig
    from .interfaces import Mutator


class PoodleWork:
    """Work-in-progress data gathered into single structure for easy passing between functions."""

    def __init__(self, config: PoodleConfig) -> None:
        """Init from PoodleConfig."""
        self.config = config
        self.folder_zips: dict[Path, Path] = {}
        self.mutators: list[Mutator | Callable] = []
        self.runner: Callable = lambda *_, **__: None
        self.reporters: list[Callable] = []

        self._echo_wrapper = EchoWrapper(config.echo_enabled, config.echo_no_color)
        self.echo: Callable = self._echo_wrapper.echo

        def number_generator() -> Generator[int, Any, None]:
            i = 1
            while True:
                yield i
                i += 1

        self._num_gen = number_generator()

    def next_num(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self._num_gen))


@dataclass
class EchoWrapper:
    """Contains config options related to echo function."""

    echo_enabled: bool | None
    echo_no_color: bool | None

    def echo(  # noqa: PLR0913
        self,
        message: Any | None = None,  # noqa: ANN401
        file: IO[AnyStr] | None = None,
        nl: bool = True,
        err: bool = False,
        color: bool | None = None,
        **styles: dict,
    ) -> None:
        """Calls 'click.secho' with settings from config."""  # noqa: D401
        if self.echo_no_color:
            color = False
        if self.echo_enabled:
            click.secho(message, file, nl, err, color, **styles)
