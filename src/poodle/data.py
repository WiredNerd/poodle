"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generator

if TYPE_CHECKING:
    from pathlib import Path

    from poodle.mutate import Mutator


@dataclass
class PoodleConfig:
    """Configuration options resolved from command line and config files."""

    config_file: Path | None
    source_folders: list[Path]
    file_filters: list[str]
    file_copy_filters: list[str]
    work_folder: Path

    mutator_opts: dict
    skip_mutators: list[str]
    add_mutators: list[str | Callable | Mutator | type]

    runner_opts: dict


class PoodleWork:
    """Work-in-progress data gathered into single structure for easy passing between functions."""

    mutators: list[Mutator | Callable] = []

    def __init__(self, config: PoodleConfig) -> PoodleWork:
        """Init from PoodleConfig."""
        self.config = config
        self.folder_zips: dict[str, Path] = {}

        def number_generator() -> Generator[int]:
            i = 1
            while True:
                yield i
                i += 1

        self._num_gen = number_generator()

    def next_num(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self._num_gen))


@dataclass
class FileMutation:
    """Mutation instructions for the current file."""

    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    text: str


@dataclass
class Mutant(FileMutation):
    """Mutation instructions for a specific file and folder."""

    source_folder: Path
    source_file: Path | None


@dataclass
class MutantTrialResult:
    """Mutation Trial Result for a Mutant."""

    passed: bool
    reason_code: str
    reason_desc: str | None = None

    RC_FOUND = "mutant_found"
    RC_NOT_FOUND = "mutant_not_found"
    RC_TIMEOUT = "timeout"
    RC_INCOMPLETE = "incomplete"
    RC_OTHER = "other"


@dataclass
class MutantTrial:
    """Trial Result for a Mutant."""

    mutant: Mutant
    result: MutantTrialResult
