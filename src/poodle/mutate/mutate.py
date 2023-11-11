"""Create Mutants."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
from typing import Callable

from poodle import PoodleInputError
from poodle.data import FileMutation, Mutant, PoodleWork
from poodle.mutate import Mutator
from poodle.mutate.bin_op import BinaryOperationMutator
from poodle.util import files_list_for_folder

standard_mutators = {
    "BinOp": BinaryOperationMutator,
}


def initialize_mutators(work: PoodleWork):
    mutators = [mutator for name, mutator in standard_mutators.items() if name not in work.config.skip_mutators]
    mutators.extend(work.config.add_mutators)

    return [init_mutator(work, mut_def) for mut_def in mutators]


def init_mutator(work: PoodleWork, mutator_def: str | Callable | Mutator | type):
    if isinstance(mutator_def, str):
        parts = mutator_def.split(".")
        module_str = ".".join(parts[:-1])
        obj_def = parts[-1:][0]
        print(module_str, obj_def)
        module = __import__(module_str, fromlist=[obj_def])
        mutator_def = getattr(module, obj_def)

    if isinstance(mutator_def, type):
        return mutator_def(config=work.config)
    if isinstance(mutator_def, Mutator) or isinstance(mutator_def, Callable):
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
    * Compile list of Mutants."""

    parsed_ast = ast.parse(file.read_bytes(), file)

    def call_mutator(mutator: Callable | Mutator) -> list[FileMutation]:
        if isinstance(mutator, Mutator):
            return mutator.create_mutations(parsed_ast=deepcopy(parsed_ast))
        else:
            return mutator(config=work.config, parsed_ast=deepcopy(parsed_ast))

    mutant_nested_list = [call_mutator(mutator) for mutator in work.mutators]
    file_mutants = [mutant for mutant_list in mutant_nested_list if mutant_list for mutant in mutant_list]

    return [Mutant(source_folder=folder, source_file=file, **vars(file_mutant)) for file_mutant in file_mutants]
