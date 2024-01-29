from __future__ import annotations

import ast
from pathlib import Path
from types import ModuleType
from typing import Any

import pluggy

from .config import PoodleConfigData
from .data import FileMutation, Mutant, TestingResults, RunResult
from .echo_wrapper import EchoWrapper
from .option_collector import PoodleOptionCollector

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
    secho: EchoWrapper,
) -> None:
    """Configure Plugin.

    :param config: poodle.PoodleConfigData object.
    :param poodle_config: poodle_config.py module, if found.
    :param cmd_kwargs: kwargs from Command Line.
    :param secho: wrapper for click.secho function."""


@hookspec()
def create_mutations(
    parsed_ast: ast.Module,
    file_lines: list[str],
    config: PoodleConfigData,
    secho: EchoWrapper,
) -> list[FileMutation]:
    """Create a list of Mutants for the provided parsed Module

    :param parsed_ast: ast.Module object.
    :param file_lines: list of lines from file.
    :param config: poodle.PoodleConfigData object.
    :param secho: wrapper for click.secho function."""


@hookspec()
def filter_mutations(
    mutants: list[Mutant],
    config: PoodleConfigData,
    secho: EchoWrapper,
) -> None:
    """Called after all mutants are created.  May modify the list of mutations in place.

    :param mutations: list of poodle.Mutant objects.
    :param config: poodle.PoodleConfigData object.
    :param secho: wrapper for click.secho function."""


@hookspec(firstresult=True)
def run_testing(
    run_folder: Path,
    timeout: float | None,
    config: PoodleConfigData,
    secho: EchoWrapper,
    source_folder: Path,
    mutant: Mutant | None,
) -> RunResult | None:
    """Run the test suite.

    :param run_folder: path to run folder.
    :param timeout: timeout in seconds.
    :param config: poodle.PoodleConfigData object.
    :param secho: wrapper for click.secho function.
    :param source_folder: path to source folder.
    :param mutant: poodle.Mutant object or none for clean run."""


@hookspec()
def report_results(
    testing_results: TestingResults,
    config: PoodleConfigData,
    secho: EchoWrapper,
) -> None:  # type: ignore [empty-body]
    """Report on Testing Results.

    :param testing_results: poodle.TestingResults object.
    :param poodle_config: poodle.PoodleConfigData object.
    :param secho: wrapper for click.secho function."""
