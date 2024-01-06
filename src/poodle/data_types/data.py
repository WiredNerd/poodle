"""Shared Data Classes used by Poodle."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from poodle import util

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass
class PoodleSerialize:
    """Base Class for Data Classes that need to be serialized to JSON."""

    @staticmethod
    def from_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Correct fields in Dictionary for JSON deserialization."""
        return d

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class PoodleConfig:
    """Configuration options resolved from command line and config files."""

    project_name: str | None
    project_version: str | None

    config_file: Path | None
    source_folders: list[Path]

    only_files: list[str]
    file_flags: int | None
    file_filters: list[str]

    file_copy_flags: int | None
    file_copy_filters: list[str]
    work_folder: Path

    max_workers: int | None

    log_format: str
    log_level: int | str
    echo_enabled: bool | None
    echo_no_color: bool | None

    mutator_opts: dict
    skip_mutators: list[str]
    add_mutators: list[Any]

    min_timeout: int
    timeout_multiplier: int
    runner: str
    runner_opts: dict

    reporters: list[str]
    reporter_opts: dict

    fail_under: float | None


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
class Mutant(FileMutation, PoodleSerialize):
    """Mutation instructions for a specific file and folder."""

    source_folder: Path
    source_file: Path | None
    unified_diff: str | None = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Correct fields in Dictionary for JSON deserialization."""
        if "source_folder" in d:
            d["source_folder"] = Path(d["source_folder"])
        if "source_file" in d and d["source_folder"] is not None:
            d["source_file"] = Path(d["source_file"])
        return d

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for JSON serialization."""
        d = asdict(self)
        d["source_folder"] = str(self.source_folder)
        if isinstance(self.source_file, Path):
            d["source_file"] = str(self.source_file)
        return d


@dataclass
class MutantTrialResult(PoodleSerialize):
    """Mutation Trial Result for a Mutant."""

    found: bool
    reason_code: str
    reason_desc: str | None = None

    RC_FOUND = "Mutant Found"
    RC_NOT_FOUND = "Mutant Not Found"
    RC_TIMEOUT = "Trial Exceeded Timeout"
    RC_INCOMPLETE = "Testing Incomplete"
    RC_OTHER = "Other, See Description"


@dataclass
class MutantTrial(PoodleSerialize):
    """Trial Result for a Mutant."""

    mutant: Mutant
    result: MutantTrialResult
    duration: float

    @staticmethod
    def from_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Correct fields in Dictionary for JSON deserialization."""
        if "mutant" in d:
            d["mutant"] = Mutant(**Mutant.from_dict(d["mutant"]))
        if "result" in d:
            d["result"] = MutantTrialResult(**d["result"])
        return d

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for JSON serialization."""
        d = asdict(self)
        d["mutant"] = self.mutant.to_dict()
        d["result"] = self.result.to_dict()
        return d


@dataclass
class TestingSummary(PoodleSerialize):
    """Summary Statistics for a Test Run."""

    trials: int = 0
    tested: int = 0
    found: int = 0
    not_found: int = 0
    timeout: int = 0
    errors: int = 0

    @property
    def success_rate(self) -> float:
        """Return the success rate of the test run."""
        if self.trials > 0:
            return self.found / self.trials
        if self.tested > 0:
            return self.found / self.tested
        return 0.0

    @property
    def coverage_display(self) -> str:
        """Return a formatted string for the coverage percentage."""
        return util.display_percent(self.success_rate)

    def __iadd__(self, result: MutantTrialResult) -> Self:
        """Update Testing Summary with data from MutantTrialResult."""
        if isinstance(result, MutantTrialResult):
            self.tested += 1
            if result.found:
                self.found += 1
            elif result.reason_code == MutantTrialResult.RC_NOT_FOUND:
                self.not_found += 1
            elif result.reason_code == MutantTrialResult.RC_TIMEOUT:
                self.timeout += 1
            else:
                self.errors += 1

        return self

    @staticmethod
    def from_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Correct fields in Dictionary for JSON deserialization."""
        d.pop("success_rate", None)
        d.pop("coverage_display", None)
        return d

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for JSON serialization."""
        d = asdict(self)
        d["success_rate"] = self.success_rate
        d["coverage_display"] = self.coverage_display
        return d


@dataclass
class TestingResults(PoodleSerialize):
    """Collection of all trials and summary statistics."""

    mutant_trials: list[MutantTrial]
    summary: TestingSummary

    @staticmethod
    def from_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Correct fields in Dictionary for JSON deserialization."""
        if "mutant_trials" in d:
            d["mutant_trials"] = [MutantTrial(**MutantTrial.from_dict(trial)) for trial in d["mutant_trials"]]
        if "summary" in d and d["summary"] is not None:
            d["summary"] = TestingSummary(**TestingSummary.from_dict(d["summary"]))
        return d

    def to_dict(self) -> dict[str, Any]:
        """Convert to Dictionary for JSON serialization."""
        d = asdict(self)
        d["mutant_trials"] = [trial.to_dict() for trial in self.mutant_trials]
        d["summary"] = self.summary.to_dict() if self.summary is not None else None
        return d
