"""Create Mutants."""

from __future__ import annotations

import ast
import logging
import re
from copy import deepcopy
from typing import TYPE_CHECKING, Callable

import pluggy

from . import FileMutation, Mutant, Mutator, PoodleConfigData, PoodleInputError, PoodleWork
from .common import util
from .common.util import files_list_for_folder

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def create_mutants_for_all_mutators(
    work: PoodleWork, config_data: PoodleConfigData, pm: pluggy.PluginManager
) -> list[Mutant]:
    """Create consolidated, flattened list of all mutants to be tried."""
    return [
        mutant
        for folder, files in get_target_files(work).items()
        for file in files
        for mutant in create_mutants_for_file(
            work=work,
            config_data=config_data,
            folder=folder,
            file=file,
            pm=pm,
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


def create_mutants_for_file(
    work: PoodleWork, config_data: PoodleConfigData, folder: Path, file: Path, pm: pluggy.PluginManager
) -> list[Mutant]:
    """Create all mutants for specified file.

    * Parse ast from file.
    * Pass file ast to all mutators.
    * Apply Filters.
    * Compile list of Mutants.
    """
    logger.debug("Create Mutants for file %s", file)

    parsed_ast = ast.parse(file.read_bytes(), file)
    util.add_parent_attr(parsed_ast)
    file_lines = file.read_text("utf-8").splitlines()

    def call_mutator(mutator: Callable | Mutator) -> list[FileMutation]:
        if isinstance(mutator, Mutator):
            return mutator.create_mutations(parsed_ast=deepcopy(parsed_ast), file_lines=deepcopy(file_lines))
        return mutator(config=work.config, parsed_ast=deepcopy(parsed_ast), file_lines=deepcopy(file_lines))

    parsed_ast_plugin_copy = deepcopy(parsed_ast)
    file_lines_plugin_copy = deepcopy(file_lines)
    mutant_nested_list = pm.hook.create_mutations(
        parsed_ast=parsed_ast_plugin_copy, file_lines=file_lines_plugin_copy, config=config_data
    )
    if ast.dump(parsed_ast_plugin_copy, include_attributes=True) != ast.dump(parsed_ast, include_attributes=True):
        raise PoodleInputError(
            "Plugin Mutators may not modify the parsed_ast.",
            "Ensure no plugin mutators modify the parsed_ast.",
        )
    if file_lines_plugin_copy != file_lines:
        raise PoodleInputError(
            "Plugin Mutators may not modify the file_lines.",
            "Ensure no plugin mutators modify the file_lines.",
        )

    file_mutants = [mutant for mutant_list in mutant_nested_list for mutant in mutant_list]

    line_filters = parse_filters(file_lines, config_data.mutator_filter_patterns)
    file_mutants = [mut for mut in file_mutants if not is_filtered(line_filters, mut)]

    return [Mutant(source_folder=folder, source_file=file, **vars(file_mutant)) for file_mutant in file_mutants]


def parse_filters(file_lines: list[str], filter_patterns: list[str]) -> dict[int, set[str]]:
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
        # pragma filter
        if re.search(r"#\s*pragma:\s*no mutate[\s#$]*", line):
            add_line_filter(line_filters, lineno, "all")

        # nomut filters
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

        # filter patterns
        for filter in filter_patterns:
            if re.search(filter, line):
                add_line_filter(line_filters, lineno, "all")

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
