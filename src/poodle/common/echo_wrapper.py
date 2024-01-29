"""Containers for Work-in-progress data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import IO, Any, AnyStr

import click


@dataclass
class EchoWrapper:
    """Contains config options related to echo function."""

    echo_enabled: bool | None
    echo_no_color: bool | None

    def __call__(  # noqa: PLR0913
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
