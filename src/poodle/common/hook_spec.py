from __future__ import annotations

from types import ModuleType
from typing import Any, Callable

import pluggy

from .base import PoodleOptionCollector
from .config import PoodleConfigData
from .data import TestingResults

hookspec = pluggy.HookspecMarker("poodle")


@hookspec()
def add_options(options: PoodleOptionCollector) -> None:
    """Add Command Line Options."""


@hookspec()
def configure(config: PoodleConfigData, poodle_config: ModuleType | None, cmd_kwargs: dict[str, Any]) -> None:
    """Configure Plugin.

    :param config: poodle.PoodleConfig object.
    :param poodle_config: poodle_config.py module, if found.
    :param cmd_kwargs: kwargs from Command Line."""


@hookspec()
def report_results(testing_results: TestingResults, config: PoodleConfigData, secho: Callable) -> None:  # type: ignore [empty-body]
    """Report on Testing Results.

    :param testing_results: poodle.TestingResults object.
    :param poodle_config: poodle.PoodleConfig object.
    :param secho: wrapper for click.secho function."""
