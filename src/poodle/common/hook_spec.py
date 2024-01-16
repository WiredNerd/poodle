from __future__ import annotations

import ast
from types import ModuleType
from typing import Any, Callable

import pluggy

from .base import PoodleOptionCollector
from .config import PoodleConfigData
from .data import FileMutation, Mutant, TestingResults

hookspec = pluggy.HookspecMarker("poodle")


@hookspec(historic=True)
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Other Plugins."""


@hookspec()
def add_options(options: PoodleOptionCollector) -> None:
    """Add Command Line Options."""


@hookspec()
def configure(
    config: PoodleConfigData,
    poodle_config: ModuleType | None,
    cmd_kwargs: dict[str, Any],
    secho: Callable,
) -> None:
    """Configure Plugin.

    :param config: poodle.PoodleConfigData object.
    :param poodle_config: poodle_config.py module, if found.
    :param cmd_kwargs: kwargs from Command Line.
    :param secho: wrapper for click.secho function."""


@hookspec()
def create_mutations(parsed_ast: ast.Module, file_lines: list[str], config: PoodleConfigData) -> list[FileMutation]:
    """Create a list of Mutants for the provided parsed Module

    :param parsed_ast: ast.Module object.
    :param file_lines: list of lines from file.
    :param config: poodle.PoodleConfigData object."""


@hookspec()
def filter_mutations(mutants: list[Mutant], config: PoodleConfigData) -> None:
    """Called after all mutants are created.  May modify the list of mutations in place.

    :param mutations: list of poodle.Mutant objects.
    :param config: poodle.PoodleConfigData object."""


@hookspec()
def report_results(testing_results: TestingResults, config: PoodleConfigData, secho: Callable) -> None:  # type: ignore [empty-body]
    """Report on Testing Results.

    :param testing_results: poodle.TestingResults object.
    :param poodle_config: poodle.PoodleConfigData object.
    :param secho: wrapper for click.secho function."""
