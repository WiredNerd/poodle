"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class PoodleConfig:
    """Configuration Options resolved from command line and config files."""

    config_file: Path | None
    source_folders: list[Path]
    file_filters: list[str]
    work_folder: Path
    runner_opts: dict
    mutator_opts: dict


class PoodleWork:
    """Work-in-progress data gathered into single structure for easy passing between functions."""

    def __init__(self, config: PoodleConfig) -> PoodleWork:
        """Init from PoodleConfig."""
        self.config = config
        self.folder_zips: dict[str, Path] = {}
        self.num_seq = self.number_sequence()

    def next_num(self) -> str:
        """Return the next value from Sequence as a string."""
        return str(next(self.num_seq))

    def number_sequence(self) -> int:
        """Generate sequence of numbers."""
        i = 1
        while True:
            yield i
            i += 1


@dataclass
class Mutant:
    """Output of Mutator functions detailing what to change."""

    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    text: str


@dataclass
class SourceFileMutant(Mutant):
    """File and Folder information with Mutation details."""

    source_folder: Path
    source_file: Path

    @classmethod
    def from_mutant(cls, source_folder: Path, source_file: Path, mutant: Mutant) -> SourceFileMutant:
        """Create SourceFileMutant using folder, file, and data from Mutant."""
        return cls(
            source_folder=source_folder,
            source_file=source_file,
            lineno=mutant.lineno,
            col_offset=mutant.col_offset,
            end_lineno=mutant.end_lineno,
            end_col_offset=mutant.end_col_offset,
            text=mutant.text,
        )


@dataclass
class PoodleTestResult:
    """Mutation Test Result for a SourceFileMutant."""

    test_passed: bool
    reason_code: str
    reason_desc: str | None = None

    RC_FOUND = "mutant_found"
    RC_NOT_FOUND = "mutant_not_found"
    RC_TIMEOUT = "timeout"
    RC_INCOMPLETE = "incomplete"
    RC_OTHER = "other"
