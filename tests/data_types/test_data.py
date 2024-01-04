from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poodle.data_types.data import (
    FileMutation,
    Mutant,
    MutantTrial,
    MutantTrialResult,
    PoodleConfig,
    TestingResults,
    TestingSummary,
)
from poodle.util import from_json, to_json


@dataclass
class PoodleConfigStub(PoodleConfig):
    project_name: str | None = None
    project_version: str | None = None

    config_file: Path | None = None
    source_folders: list[Path] = None  # type: ignore [assignment]

    only_files: list[str] = None  # type: ignore [assignment]
    file_flags: int = None  # type: ignore [assignment]
    file_filters: list[str] = None  # type: ignore [assignment]

    file_copy_flags: int = None  # type: ignore [assignment]
    file_copy_filters: list[str] = None  # type: ignore [assignment]
    work_folder: Path = None  # type: ignore [assignment]

    max_workers: int | None = None

    log_format: str = None  # type: ignore [assignment]
    log_level: int | str = None  # type: ignore [assignment]
    echo_enabled: bool = None  # type: ignore [assignment]
    echo_no_color: bool = None  # type: ignore [assignment]

    mutator_opts: dict = None  # type: ignore [assignment]
    skip_mutators: list[str] = None  # type: ignore [assignment]
    add_mutators: list[Any] = None  # type: ignore [assignment]

    min_timeout: int = None  # type: ignore [assignment]
    timeout_multiplier: int = None  # type: ignore [assignment]
    runner: str = None  # type: ignore [assignment]
    runner_opts: dict = None  # type: ignore [assignment]

    reporters: list[str] = None  # type: ignore [assignment]
    reporter_opts: dict = None  # type: ignore [assignment]

    fail_under: float | None = None


class TestPoodleConfig:
    @staticmethod
    def create_poodle_config():
        return PoodleConfig(
            project_name="example",
            project_version="1.2.3",
            config_file=Path("filename.toml"),
            source_folders=[Path("src")],
            only_files=["example.py"],
            file_flags=4,
            file_filters=["test_"],
            file_copy_flags=5,
            file_copy_filters=["skip"],
            work_folder=Path(".poodle"),
            max_workers=3,
            log_format="$(message)s",
            log_level=0,
            echo_enabled=True,
            echo_no_color=False,
            mutator_opts={"bin_op_level": 2},
            skip_mutators=["null"],
            add_mutators=["custom"],
            min_timeout=15,
            timeout_multiplier=10,
            runner="command_line",
            runner_opts={"command_line": "pytest tests"},
            reporters=["summary"],
            reporter_opts={"summary": "value"},
            fail_under=95.0,
        )

    def test_poodle_config(self):
        config = self.create_poodle_config()

        assert config.project_name == "example"
        assert config.project_version == "1.2.3"

        assert config.config_file == Path("filename.toml")
        assert config.source_folders == [Path("src")]

        assert config.only_files == ["example.py"]
        assert config.file_flags == 4
        assert config.file_filters == ["test_"]

        assert config.file_copy_flags == 5
        assert config.file_copy_filters == ["skip"]
        assert config.work_folder == Path(".poodle")

        assert config.max_workers == 3

        assert config.log_format == "$(message)s"
        assert config.log_level == 0
        assert config.echo_enabled is True
        assert config.echo_no_color is False

        assert config.mutator_opts == {"bin_op_level": 2}
        assert config.skip_mutators == ["null"]
        assert config.add_mutators == ["custom"]

        assert config.min_timeout == 15
        assert config.timeout_multiplier == 10
        assert config.runner == "command_line"
        assert config.runner_opts == {"command_line": "pytest tests"}

        assert config.reporters == ["summary"]
        assert config.reporter_opts == {"summary": "value"}

        assert config.fail_under == 95.0


class TestFileMutation:
    @staticmethod
    def create_file_mutation():
        return FileMutation(
            mutator_name="test",
            lineno=1,
            col_offset=2,
            end_lineno=3,
            end_col_offset=4,
            text="mutant",
        )

    def test_file_mutant(self):
        file_mutant = self.create_file_mutation()

        assert file_mutant.lineno == 1
        assert file_mutant.col_offset == 2
        assert file_mutant.end_lineno == 3
        assert file_mutant.end_col_offset == 4
        assert file_mutant.text == "mutant"


class TestMutant:
    def test_init(self):
        poodle_mutant = Mutant(
            source_folder=Path("src"),
            source_file=Path("test.py"),
            **vars(TestFileMutation.create_file_mutation()),
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file == Path("test.py")
        assert poodle_mutant.lineno == 1
        assert poodle_mutant.col_offset == 2
        assert poodle_mutant.end_lineno == 3
        assert poodle_mutant.end_col_offset == 4
        assert poodle_mutant.text == "mutant"

    def test_poodle_mutant_min(self):
        poodle_mutant = Mutant(
            mutator_name="test",
            source_folder=Path("src"),
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        )

        assert poodle_mutant.mutator_name == "test"
        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file is None
        assert poodle_mutant.lineno == 0
        assert poodle_mutant.col_offset == 0
        assert poodle_mutant.end_lineno == 0
        assert poodle_mutant.end_col_offset == 0
        assert poodle_mutant.text == ""

    def mutant_object(self):
        return Mutant(
            mutator_name="test",
            lineno=1,
            col_offset=2,
            end_lineno=3,
            end_col_offset=4,
            text="mutant",
            source_folder=Path("src"),
            source_file=Path("test.py"),
            unified_diff="diff",
        )

    def mutant_dict(self):
        return {
            "mutator_name": "test",
            "lineno": 1,
            "col_offset": 2,
            "end_lineno": 3,
            "end_col_offset": 4,
            "text": "mutant",
            "source_folder": "src",
            "source_file": "test.py",
            "unified_diff": "diff",
        }

    def test_serialize(self):
        mutant = self.mutant_object()
        expected = self.mutant_dict()
        assert mutant.to_dict() == expected
        assert to_json(mutant) == json.dumps(expected)

    def test_deserialize(self):
        mutant = json.dumps(self.mutant_dict())
        expected = self.mutant_object()
        assert from_json(mutant, Mutant) == expected


class TestMutantTrialResult:
    def test_mutant_trial_result(self):
        result = MutantTrialResult(found=True, reason_code="test", reason_desc="it worked")

        assert result.found is True
        assert result.reason_code == "test"
        assert result.reason_desc == "it worked"
        assert result.RC_FOUND == "Mutant Found"
        assert result.RC_NOT_FOUND == "Mutant Not Found"
        assert result.RC_TIMEOUT == "Trial Exceeded Timeout"
        assert result.RC_INCOMPLETE == "Testing Incomplete"
        assert result.RC_OTHER == "Other, See Description"

    def test_mutant_trial_result_min(self):
        result = MutantTrialResult(
            found=True,
            reason_code="test",
        )

        assert result.found is True
        assert result.reason_code == "test"
        assert result.reason_desc is None

    def mutant_trial_result_object(self):
        return MutantTrialResult(
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
            reason_desc="it worked",
        )

    def mutant_trial_result_dict(self):
        return {
            "found": True,
            "reason_code": MutantTrialResult.RC_FOUND,
            "reason_desc": "it worked",
        }

    def test_serialize(self):
        result = self.mutant_trial_result_object()
        expected = self.mutant_trial_result_dict()
        assert result.to_dict() == expected
        assert to_json(result) == json.dumps(expected)

    def test_deserialize(self):
        result = json.dumps(self.mutant_trial_result_dict())
        expected = self.mutant_trial_result_object()
        assert from_json(result, MutantTrialResult) == expected


class TestMutantTrial:
    def test_mutant_trial(self):
        mutant = Mutant(source_folder=Path(), source_file=None, **vars(TestFileMutation.create_file_mutation()))
        result = MutantTrialResult(found=True, reason_code="test")
        trial = MutantTrial(mutant=mutant, result=result, duration=1.2)
        assert trial.mutant == mutant
        assert trial.result == result
        assert trial.duration == 1.2

    def mutant_trial_object(self):
        return MutantTrial(
            mutant=TestMutant().mutant_object(),
            result=TestMutantTrialResult().mutant_trial_result_object(),
            duration=1.2,
        )

    def mutant_trial_dict(self):
        return {
            "mutant": TestMutant().mutant_dict(),
            "result": TestMutantTrialResult().mutant_trial_result_dict(),
            "duration": 1.2,
        }

    def test_serialize(self):
        trial = self.mutant_trial_object()
        expected = self.mutant_trial_dict()
        assert trial.to_dict() == expected
        assert to_json(trial) == json.dumps(expected)

    def test_deserialize(self):
        trial = json.dumps(self.mutant_trial_dict())
        expected = self.mutant_trial_object()
        assert from_json(trial, MutantTrial) == expected


class TestTestingSummary:
    def test_testing_summary(self):
        testing_summary = TestingSummary(
            trials=1,
            tested=2,
            found=3,
            not_found=4,
            timeout=5,
            errors=6,
        )

        assert testing_summary.trials == 1
        assert testing_summary.tested == 2
        assert testing_summary.found == 3
        assert testing_summary.not_found == 4
        assert testing_summary.timeout == 5
        assert testing_summary.errors == 6

    def test_testing_summary_defaults(self):
        testing_summary = TestingSummary()

        assert testing_summary.trials == 0
        assert testing_summary.tested == 0
        assert testing_summary.found == 0
        assert testing_summary.not_found == 0
        assert testing_summary.timeout == 0
        assert testing_summary.errors == 0

    def test_success_rate_trials(self):
        summary = TestingSummary(trials=9, found=6)
        assert summary.success_rate == 6 / 9

    def test_success_rate_tested(self):
        summary = TestingSummary(tested=9, found=6)
        assert summary.success_rate == 6 / 9

    def test_success_rate_zero(self):
        summary = TestingSummary(found=6)
        assert summary.success_rate == 0.0

    def test_coverage_display(self):
        summary = TestingSummary(trials=9, found=6)
        assert summary.coverage_display == "66.67%"

    def test_iadd(self):
        summary = TestingSummary(trials=10)
        expected = TestingSummary(trials=10)

        summary += 1
        assert summary == expected

        summary += MutantTrialResult(True, MutantTrialResult.RC_FOUND)
        expected.tested += 1
        expected.found += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_NOT_FOUND)
        expected.tested += 1
        expected.not_found += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_TIMEOUT)
        expected.tested += 1
        expected.timeout += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_OTHER)
        expected.tested += 1
        expected.errors += 1
        assert summary == expected

        summary += MutantTrialResult(True, MutantTrialResult.RC_FOUND)
        expected.tested += 1
        expected.found += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_NOT_FOUND)
        expected.tested += 1
        expected.not_found += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_TIMEOUT)
        expected.tested += 1
        expected.timeout += 1
        assert summary == expected

        summary += MutantTrialResult(False, MutantTrialResult.RC_OTHER)
        expected.tested += 1
        expected.errors += 1
        assert summary == expected

    def test_iadd_one_trial(self):
        summary = TestingSummary()
        summary = TestingSummary(trials=1)
        expected = TestingSummary(tested=1, found=1, trials=1)

        summary += MutantTrialResult(True, MutantTrialResult.RC_FOUND)
        assert summary == expected

    def test_iadd_zero_trials(self):
        summary = TestingSummary()
        expected = TestingSummary(tested=1, found=1)

        summary += MutantTrialResult(True, MutantTrialResult.RC_FOUND)
        assert summary == expected

    def test_iadd_neg_trials(self):
        summary = TestingSummary(trials=-1)
        expected = TestingSummary(tested=1, found=1, trials=-1)

        summary += MutantTrialResult(True, MutantTrialResult.RC_FOUND)
        assert summary == expected

    def summary_object(self):
        return TestingSummary(
            trials=10,
            tested=9,
            found=8,
            not_found=7,
            timeout=6,
            errors=5,
        )

    def summary_dict(self):
        return {
            "trials": 10,
            "tested": 9,
            "found": 8,
            "not_found": 7,
            "timeout": 6,
            "errors": 5,
            "success_rate": 0.8,
            "coverage_display": "80.00%",
        }

    def test_serialize(self):
        summary = self.summary_object()
        expected = self.summary_dict()
        assert summary.to_dict() == expected
        assert to_json(summary) == json.dumps(expected)

    def test_deserialize(self):
        summary = json.dumps(self.summary_dict())
        expected = self.summary_object()
        assert from_json(summary, TestingSummary) == expected


class TestTestingResults:
    def test_testing_results(self):
        mutant = Mutant(source_folder=Path(), source_file=None, **vars(TestFileMutation.create_file_mutation()))
        result = MutantTrialResult(found=True, reason_code="test")
        trial = MutantTrial(mutant=mutant, result=result, duration=1.2)
        testing_summary = TestingSummary(trials=4)
        results = TestingResults(
            mutant_trials=[trial],
            summary=testing_summary,
        )

        assert results.summary == testing_summary
        assert results.mutant_trials == [trial]

    def results_object(self):
        return TestingResults(
            mutant_trials=[TestMutantTrial().mutant_trial_object()],
            summary=TestTestingSummary().summary_object(),
        )

    def results_dict(self):
        return {
            "mutant_trials": [TestMutantTrial().mutant_trial_dict()],
            "summary": TestTestingSummary().summary_dict(),
        }

    def test_serialize(self):
        results = self.results_object()
        expected = self.results_dict()
        assert results.to_dict() == expected
        assert to_json(results) == json.dumps(expected)

    def test_deserialize(self):
        results = json.dumps(self.results_dict())
        expected = self.results_object()
        assert from_json(results, TestingResults) == expected

    def test_serialize_no_summary(self):
        results = self.results_object()
        results.summary = None
        expected = self.results_dict()
        expected["summary"] = None
        assert results.to_dict() == expected
        assert to_json(results) == json.dumps(expected)

    def test_deserialize_no_summary(self):
        results_dict = self.results_dict()
        results_dict["summary"] = None
        results = json.dumps(results_dict)
        expected = self.results_object()
        expected.summary = None
        assert from_json(results, TestingResults) == expected
