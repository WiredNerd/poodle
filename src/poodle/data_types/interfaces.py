"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .data import FileMutation, Mutant, MutantTrialResult, PoodleConfig, TestingResults

if TYPE_CHECKING:
    import ast
    from pathlib import Path


def create_mutations(config: PoodleConfig, parsed_ast: ast.Module, **_) -> list[FileMutation]:  # type: ignore [empty-body] # noqa: ARG001
    """Create a list of Mutants for the provided parsed Module.

    This will be called once with parsed ast for each Module.
    """


class Mutator(ABC):
    """Abstract class for Mutators."""

    def __init__(self, config: PoodleConfig, **_) -> None:
        """Initialize PoodleMutator."""
        self.config = config

    @abstractmethod
    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Create a list of Mutants for the provided parsed Module.

        This will be called once with parsed ast for each Module.
        """


# runner method signature:
def runner(config: PoodleConfig, run_folder: Path, mutant: Mutant, **_) -> MutantTrialResult:  # type: ignore [empty-body] # noqa: ARG001
    """Run trial of mutant in specified folder.

    Files from the source folder have been copied to the run folder, and mutation has been applied.
    """


# reporter method signature:
def reporter(config: PoodleConfig, testing_results: TestingResults, **_) -> None:  # type: ignore [empty-body] # noqa: ARG001
    """Report on Testing Results."""
