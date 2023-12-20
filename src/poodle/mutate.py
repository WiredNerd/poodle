"""Create Mutants."""

from __future__ import annotations

import ast
import logging
import re
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from . import PoodleInputError
from .data_types import FileMutation, Mutant, Mutator, PoodleWork
from .mutators import (
    AugAssignMutator,
    BinaryOperationMutator,
    ComparisonMutator,
    DecoratorMutator,
    DictArrayCallMutator,
    FunctionCallMutator,
    KeywordMutator,
    LambdaReturnMutator,
    NumberMutator,
    ReturnMutator,
    StringMutator,
    UnaryOperationMutator,
)
from .util import dynamic_import, files_list_for_folder

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

builtin_mutators = {
    BinaryOperationMutator.mutator_name: BinaryOperationMutator,
    AugAssignMutator.mutator_name: AugAssignMutator,
    UnaryOperationMutator.mutator_name: UnaryOperationMutator,
    ComparisonMutator.mutator_name: ComparisonMutator,
    KeywordMutator.mutator_name: KeywordMutator,
    NumberMutator.mutator_name: NumberMutator,
    StringMutator.mutator_name: StringMutator,
    FunctionCallMutator.mutator_name: FunctionCallMutator,
    DictArrayCallMutator.mutator_name: DictArrayCallMutator,
    LambdaReturnMutator.mutator_name: LambdaReturnMutator,
    ReturnMutator.mutator_name: ReturnMutator,
    DecoratorMutator.mutator_name: DecoratorMutator,
}


def initialize_mutators(work: PoodleWork) -> list[Callable | Mutator]:
    """Initialize all mutators from standard list and from config options."""
    mutators: list[Any] = [
        mutator for name, mutator in builtin_mutators.items() if name not in work.config.skip_mutators
    ]
    mutators.extend(work.config.add_mutators)

    return [initialize_mutator(work, mut_def) for mut_def in mutators]


def initialize_mutator(work: PoodleWork, mutator_def: Any) -> Callable | Mutator:  # noqa: ANN401
    """Import and initialize a Mutator.

    mutator_def may be string of object to import, Callable, Mutator subclass or Mutator subclass instance.
    """
    logger.debug(mutator_def)

    if isinstance(mutator_def, str):
        try:
            mutator_def = dynamic_import(mutator_def)
        except Exception as ex:  # noqa: BLE001
            msg = f"Import failed for mutator '{mutator_def}'"
            raise PoodleInputError(msg) from ex

    if isinstance(mutator_def, type) and issubclass(mutator_def, Mutator):
        return mutator_def(config=work.config, echo=work.echo)

    if callable(mutator_def) or isinstance(mutator_def, Mutator):
        return mutator_def

    msg = (
        f"Unable to create mutator '{mutator_def}' of type={type(mutator_def)}. "
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
    logger.debug(
        "get_target_files source_folders=%s only_files=%s file_filters=%s",
        work.config.source_folders,
        work.config.only_files,
        work.config.source_folders,
    )

    if work.config.only_files:
        out: dict[Path, list[Path]] = {}
        for folder in work.config.source_folders:
            out[folder] = []
            for glob in work.config.only_files:
                out[folder] += files_list_for_folder(
                    folder=folder,
                    match_glob=glob,
                    flags=work.config.file_flags,
                    filter_globs=[],
                )
        return out
    return {
        folder: files_list_for_folder(
            folder=folder,
            match_glob="*.py",
            flags=work.config.file_flags,
            filter_globs=work.config.file_filters,
        )
        for folder in work.config.source_folders
    }


def create_mutants_for_file(work: PoodleWork, folder: Path, file: Path) -> list[Mutant]:
    """Create all mutants for specified file.

    * Parse ast from file.
    * Pass file ast to all mutators.
    * Apply Filters.
    * Compile list of Mutants.
    """
    logger.debug("Create Mutants for file %s", file)

    parsed_ast = ast.parse(file.read_bytes(), file)
    file_lines = file.read_text("utf-8").splitlines()

    def call_mutator(mutator: Callable | Mutator) -> list[FileMutation]:
        if isinstance(mutator, Mutator):
            return mutator.create_mutations(parsed_ast=deepcopy(parsed_ast), file_lines=deepcopy(file_lines))
        return mutator(config=work.config, parsed_ast=deepcopy(parsed_ast), file_lines=deepcopy(file_lines))

    mutant_nested_list = [call_mutator(mutator) for mutator in work.mutators]
    file_mutants = [mutant for mutant_list in mutant_nested_list if mutant_list for mutant in mutant_list]

    line_filters = parse_filters(file_lines)
    file_mutants = [mut for mut in file_mutants if not is_filtered(line_filters, mut)]

    return [Mutant(source_folder=folder, source_file=file, **vars(file_mutant)) for file_mutant in file_mutants]


def parse_filters(file_lines: list[str]) -> dict[int, set[str]]:
    r"""Parse text for comments to filter mutations.

    Block all mutations:

    \# pragma: no mutate

    \# nomut

    \# nomut: start

    \# nomut: end

    Block only specific mutations:

    \# nomut: mutator,mutator
    """
    line_filters: dict[int, set[str]] = {}

    no_mut_on = False

    for lineno, line in enumerate(file_lines, start=1):
        if re.search(r"#\s*pragma:\s*no mutate[\s#$]*", line):
            add_line_filter(line_filters, lineno, "all")
        no_mut_filter: list[str] = re.findall(r"#\s*nomut:?\s*([A-Za-z0-9,\s]*)[#$]*", line)

        if no_mut_filter and no_mut_filter[0].strip().lower() in ("start", "on"):
            no_mut_on = True

        if no_mut_on:
            add_line_filter(line_filters, lineno, "all")
        else:
            for mutators in no_mut_filter:
                for mutator in mutators.split(","):
                    add_line_filter(line_filters, lineno, mutator.strip())

        if no_mut_filter and no_mut_filter[0].strip().lower() in ("end", "off"):
            no_mut_on = False

    return line_filters


def add_line_filter(line_filters: dict[int, set[str]], lineno: int, mutator: str) -> None:
    """Add filter to line_filters dict."""
    if lineno not in line_filters:
        line_filters[lineno] = set()
    line_filters[lineno].add("all" if mutator == "" else mutator.lower())


def is_filtered(line_filters: dict[int, set[str]], file_mutant: FileMutation) -> bool:
    """Identify if this mutant matches any filters."""
    for lineno in range(file_mutant.lineno, file_mutant.end_lineno + 1):
        if lineno in line_filters and (
            "all" in line_filters[lineno] or file_mutant.mutator_name.lower() in line_filters[lineno]
        ):
            return True
    return False
