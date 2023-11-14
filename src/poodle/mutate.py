"""Create Mutants."""

from __future__ import annotations

import ast
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from . import PoodleInputError
from .mutators.bin_op import BinaryOperationMutator
from .types import FileMutation, Mutant, Mutator, PoodleWork
from .util import dynamic_import, files_list_for_folder

if TYPE_CHECKING:
    from pathlib import Path

builtin_mutators = {
    "BinOp": BinaryOperationMutator,
}


def initialize_mutators(work: PoodleWork) -> list[Callable | Mutator]:
    """Initialize all mutators from standard list and from config options."""
    mutators: list[Any] = [
        mutator for name, mutator in builtin_mutators.items() if name not in work.config.skip_mutators
    ]
    mutators.extend(work.config.add_mutators)

    return [init_mutator(work, mut_def) for mut_def in mutators]


def init_mutator(work: PoodleWork, mutator_def: Any) -> Callable | Mutator:  # noqa: ANN401
    """Import and initialize a Mutator.

    mutator_def may be string of object to import, Callable, Mutator subclass or Mutator subclass instance.
    """
    if isinstance(mutator_def, str):
        mutator_def = dynamic_import(mutator_def)

    if isinstance(mutator_def, type) and issubclass(mutator_def, Mutator):
        return mutator_def(config=work.config)
    if callable(mutator_def) or isinstance(mutator_def, Mutator):
        return mutator_def

    msg = (
        f"Unable to create mutator '{mutator_def}' of type={type(mutator_def)}."
        "Expected String, Callable, Mutator subclass or Mutator subclass instance."
    )
    raise PoodleInputError(msg)


def create_mutants_for_all_mutators(work: PoodleWork) -> list[Mutant]:
    """Create consolidated, flattened list of all mutants to be tried."""
    return [
        mutant
        for folder, files in get_target_files(work).items()
        for file in files
        for mutant in create_mutants_for_file(
            work,
            folder,
            file,
        )
    ]


def get_target_files(work: PoodleWork) -> dict[Path, list[Path]]:
    """Create mapping from each source folder to all mutable files in that folder."""
    return {
        folder: files_list_for_folder(
            "*.py",
            work.config.file_filters,
            folder,
        )
        for folder in work.config.source_folders
    }


def create_mutants_for_file(work: PoodleWork, folder: Path, file: Path) -> list[Mutant]:
    """Create all mutants for specified file.

    * Parse ast from file.
    * Pass file ast to all mutators.
    * TODO: Apply Filters.
    * Compile list of Mutants.
    """
    parsed_ast = ast.parse(file.read_bytes(), file)

    def call_mutator(mutator: Callable | Mutator) -> list[FileMutation]:
        if isinstance(mutator, Mutator):
            return mutator.create_mutations(parsed_ast=deepcopy(parsed_ast))
        return mutator(config=work.config, parsed_ast=deepcopy(parsed_ast))

    mutant_nested_list = [call_mutator(mutator) for mutator in work.mutators]
    file_mutants = [mutant for mutant_list in mutant_nested_list if mutant_list for mutant in mutant_list]

    return [Mutant(source_folder=folder, source_file=file, **vars(file_mutant)) for file_mutant in file_mutants]
