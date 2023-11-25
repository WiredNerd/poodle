"""Shared Data Classes used by Poodle."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from .data import FileMutation, Mutant, MutantTrialResult, PoodleConfig, TestingResults

if TYPE_CHECKING:
    from pathlib import Path


def create_mutations(config: PoodleConfig, echo: Callable, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:  # type: ignore [empty-body] # noqa: ARG001
    """Create a list of Mutants for the provided parsed Module.

    This will be called once with parsed ast for each Module.
    """


class Mutator(ABC):
    """Abstract class for Mutators."""

    def __init__(self, config: PoodleConfig, echo: Callable, *_, **__) -> None:
        """Initialize PoodleMutator."""
        self.config = config
        self.echo = echo

    @abstractmethod
    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Create a list of Mutants for the provided parsed Module.

        This will be called once with parsed ast for each Module.
        """

    def create_file_mutation(self, node: ast.AST, text: str):
        """Create a FileMutation copying location data from specified node."""
        return FileMutation(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno or node.lineno,
            end_col_offset=node.end_col_offset or node.col_offset,
            text=text,
        )

    def add_parent_attr(self, parsed_ast: ast.Module):
        for node in ast.walk(parsed_ast):
            for child in ast.iter_child_nodes(node):
                child.parent = node


# runner method signature:
def runner(config: PoodleConfig, echo: Callable, run_folder: Path, mutant: Mutant, *_, **__) -> MutantTrialResult:  # type: ignore [empty-body] # noqa: ARG001
    """Run trial of mutant in specified folder.

    Files from the source folder have been copied to the run folder, and mutation has been applied.
    """


# reporter method signature:
def reporter(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:  # type: ignore [empty-body] # noqa: ARG001
    """Report on Testing Results."""
