"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import Self


@dataclass
class PoodleConfig:
    """Configuration options resolved from command line and config files."""

    config_file: Path | None
    source_folders: list[Path]
    only_files: list[str]
    file_filters: list[str]
    file_copy_filters: list[str]
    work_folder: Path

    max_workers: int | None

    log_format: str
    log_level: int | str
    echo_enabled: bool

    mutator_opts: dict
    skip_mutators: list[str]
    add_mutators: list[Any]

    min_timeout: int
    runner: str
    runner_opts: dict

    reporters: list[str]
    reporter_opts: dict


@dataclass
class FileMutation:
    """Mutation instructions for the current file."""

    mutator_name: str
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
    duration: float


@dataclass
class TestingSummary:
    """Summary Statistics for a Test Run."""

    trials: int = 0
    tested: int = 0
    found: int = 0
    not_found: int = 0
    timeout: int = 0
    errors: int = 0
    success_rate: float = 0.0

    def __iadd__(self, result: MutantTrialResult) -> Self:
        """Update Testing Summary with data from MutantTrialResult."""
        if isinstance(result, MutantTrialResult):
            self.tested += 1
            if result.passed:
                self.found += 1
            elif result.reason_code == MutantTrialResult.RC_NOT_FOUND:
                self.not_found += 1
            elif result.reason_code == MutantTrialResult.RC_TIMEOUT:
                self.timeout += 1
            else:
                self.errors += 1

        if self.trials > 0:
            self.success_rate = round(self.found / self.trials, 1)

        return self


@dataclass
class TestingResults:
    """Collection of all trials and summary statistics."""

    mutant_trials: list[MutantTrial]
    summary: TestingSummary
