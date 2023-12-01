"""Abstract Classes and Model functions for Mutators, Runners, and Reporters."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from .data import FileMutation, Mutant, MutantTrialResult, PoodleConfig, TestingResults

if TYPE_CHECKING:
    from pathlib import Path


def create_mutations(config: PoodleConfig, echo: Callable, parsed_ast: ast.Module, file_lines: list[str], *_, **__) -> list[FileMutation]:  # type: ignore [empty-body] # noqa: ARG001
    """Create a list of Mutants for the provided parsed Module.

    This will be called once with parsed ast for each Module.
    """


class Mutator(ABC):
    """Abstract class for Mutators."""

    def __init__(self, config: PoodleConfig, echo: Callable, *_, **__) -> None:
        """Initialize PoodleMutator."""
        self.config = config
        self.echo = echo

    mutator_name = ""

    @abstractmethod
    def create_mutations(self, parsed_ast: ast.Module, file_lines: list[str], *_, **__) -> list[FileMutation]:
        """Create a list of Mutants for the provided parsed Module.

        This will be called once with parsed ast for each Module.
        """

    @classmethod
    def create_file_mutation(cls, node: ast.AST, text: str) -> FileMutation:
        """Create a FileMutation copying location data from specified node."""
        lineno, col_offset, end_lineno, end_col_offset = cls.get_location(node)

        return FileMutation(
            mutator_name=cls.mutator_name,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
            text=text,
        )

    @staticmethod
    def get_location(node: ast.AST) -> tuple[int, int, int, int]:
        """Get location lines and columns that encompasses node and all child nodes."""
        lineno = node.lineno
        col_offset = node.col_offset
        end_lineno = node.end_lineno or node.lineno
        end_col_offset = node.end_col_offset or node.col_offset

        for n in ast.walk(node):
            if not hasattr(n, "lineno"):
                continue

            if n.lineno < lineno:
                lineno = n.lineno
                col_offset = n.col_offset
            elif n.lineno == lineno and n.col_offset < col_offset:
                col_offset = n.col_offset

            if not hasattr(n, "end_lineno") or not n.end_lineno:
                continue

            if n.end_lineno > end_lineno:
                end_lineno = n.end_lineno
                if n.end_col_offset:
                    end_col_offset = n.end_col_offset
            elif n.end_lineno == end_lineno and n.end_col_offset and n.end_col_offset > end_col_offset:
                end_col_offset = n.end_col_offset

        return (lineno, col_offset, end_lineno, end_col_offset)

    @staticmethod
    def add_parent_attr(parsed_ast: ast.Module) -> None:
        """Update all child nodes in tree with parent field."""
        for node in ast.walk(parsed_ast):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore [attr-defined]


# runner method signature:
def runner(config: PoodleConfig, echo: Callable, run_folder: Path, mutant: Mutant, *_, **__) -> MutantTrialResult:  # type: ignore [empty-body] # noqa: ARG001
    """Run trial of mutant in specified folder.

    Files from the source folder have been copied to the run folder, and mutation has been applied.
    """


# reporter method signature:
def reporter(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:  # type: ignore [empty-body] # noqa: ARG001
    """Report on Testing Results."""
