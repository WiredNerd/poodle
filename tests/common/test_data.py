from __future__ import annotations

import json
from pathlib import Path

from poodle.common.data import (
    CleanRunTrial,
    FileMutation,
    Mutant,
    MutantTrial,
    MutantTrialResult,
    RunResult,
    TestingResults,
    TestingSummary,
    from_json,
    to_json,
)


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
        file_mutant = TestFileMutation.create_file_mutation()

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
            unified_diff="diff",
            **vars(TestFileMutation.create_file_mutation()),
        )

        assert poodle_mutant.source_folder == Path("src")
        assert poodle_mutant.source_file == Path("test.py")
        assert poodle_mutant.unified_diff == "diff"

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
        assert poodle_mutant.unified_diff is None

        assert poodle_mutant.source_file is None
        assert poodle_mutant.lineno == 0
        assert poodle_mutant.col_offset == 0
        assert poodle_mutant.end_lineno == 0
        assert poodle_mutant.end_col_offset == 0
        assert poodle_mutant.text == ""
        assert poodle_mutant.unified_diff is None

    @staticmethod
    def mutant_object():
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

    @staticmethod
    def mutant_dict():
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
        mutant = TestMutant.mutant_object()
        expected = TestMutant.mutant_dict()
        assert mutant.to_dict() == expected
        assert to_json(mutant) == json.dumps(expected)

    def test_deserialize_dict(self):
        expected_dict = TestMutant.mutant_dict()
        expected_dict["source_folder"] = Path(expected_dict["source_folder"])
        expected_dict["source_file"] = Path(expected_dict["source_file"])
        assert self.mutant_object().from_dict(self.mutant_dict()) == expected_dict

    def test_deserialize_dict_na(self):
        expected_dict = TestMutant.mutant_dict()
        expected_dict["source_folder"] = Path(expected_dict["source_folder"])
        expected_dict.pop("source_file")

        mutant_dict = self.mutant_dict()
        mutant_dict.pop("source_file")
        assert self.mutant_object().from_dict(mutant_dict) == expected_dict

    def test_deserialize_dict_none(self):
        expected_dict = TestMutant.mutant_dict()
        expected_dict["source_folder"] = Path(expected_dict["source_folder"])
        expected_dict.pop("source_file")

        mutant_dict = self.mutant_dict()
        mutant_dict["source_file"] = None
        assert self.mutant_object().from_dict(mutant_dict) == expected_dict

    def test_deserialize_json(self):
        mutant = json.dumps(self.mutant_dict())
        expected = self.mutant_object()
        assert from_json(mutant, Mutant) == expected


class TestRunResult:
    def test_run_result(self):
        test_run_result = RunResult(result=RunResult.RESULT_PASSED, description="test")

        assert test_run_result.result == RunResult.RESULT_PASSED
        assert test_run_result.description == "test"

        assert RunResult.RESULT_PASSED == "All tests passed"
        assert RunResult.RESULT_FAILED == "Some tests failed"
        assert RunResult.RESULT_TIMEOUT == "Testing exceeded timeout limit"
        assert RunResult.RESULT_ERROR == "An error prevented testing completion"
        assert RunResult.RESULT_OTHER == "Other, see description"

    def test_run_result_default(self):
        test_run_result = RunResult(result=RunResult.RESULT_PASSED)

        assert test_run_result.result == RunResult.RESULT_PASSED
        assert test_run_result.description is None


class TestCleanRunTrial:
    def test_clean_run_trial(self):
        trial = CleanRunTrial(
            source_folder=Path("src"),
            result=RunResult(result=RunResult.RESULT_PASSED),
            duration=1.2,
        )

        assert trial.source_folder == Path("src")
        assert trial.result == RunResult(result=RunResult.RESULT_PASSED)
        assert trial.duration == 1.2


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

    @staticmethod
    def mutant_trial_result_object():
        return MutantTrialResult(
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
            reason_desc="it worked",
        )

    @staticmethod
    def mutant_trial_result_dict():
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

    def test_deserialize_dict(self):
        expected_dict = self.mutant_trial_result_dict()
        assert self.mutant_trial_result_object().from_dict(self.mutant_trial_result_dict()) == expected_dict

    def test_deserialize_json(self):
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

    @staticmethod
    def mutant_trial_object():
        return MutantTrial(
            mutant=TestMutant.mutant_object(),
            result=TestMutantTrialResult.mutant_trial_result_object(),
            duration=1.2,
        )

    @staticmethod
    def mutant_trial_dict():
        return {
            "mutant": TestMutant.mutant_dict(),
            "result": TestMutantTrialResult.mutant_trial_result_dict(),
            "duration": 1.2,
        }

    @staticmethod
    def mutant_trial_from_dict():
        return {
            "mutant": TestMutant.mutant_object(),
            "result": TestMutantTrialResult.mutant_trial_result_object(),
            "duration": 1.2,
        }

    def test_serialize(self):
        trial = TestMutantTrial.mutant_trial_object()
        expected = TestMutantTrial.mutant_trial_dict()
        assert trial.to_dict() == expected
        assert to_json(trial) == json.dumps(expected)

    def test_deserialize_dict(self):
        expected_dict = TestMutantTrial.mutant_trial_from_dict()
        assert self.mutant_trial_object().from_dict(TestMutantTrial.mutant_trial_dict()) == expected_dict

    def test_deserialize_json(self):
        trial = json.dumps(TestMutantTrial.mutant_trial_dict())
        expected = TestMutantTrial.mutant_trial_object()
        assert from_json(trial, MutantTrial) == expected


class TestTestingSummary:
    def testing_summary(self):
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

    def testing_summary_defaults(self):
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

    def test_success_rate_trials_one(self):
        summary = TestingSummary(trials=1, found=1)
        assert summary.success_rate == 1.0

    def test_success_rate_tested(self):
        summary = TestingSummary(tested=9, found=6)
        assert summary.success_rate == 6 / 9

    def test_success_rate_tested_one(self):
        summary = TestingSummary(tested=1, found=1)
        assert summary.success_rate == 1.0

    def test_success_rate_zero(self):
        summary = TestingSummary(found=6)
        assert summary.success_rate == 0.0

    def test_coverage_display(self):
        summary = TestingSummary(trials=9, found=6)
        assert summary.coverage_display == "66.6%"

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

    @staticmethod
    def summary_object():
        return TestingSummary(
            trials=10,
            tested=9,
            found=8,
            not_found=7,
            timeout=6,
            errors=5,
        )

    @staticmethod
    def summary_dict():
        return {
            "trials": 10,
            "tested": 9,
            "found": 8,
            "not_found": 7,
            "timeout": 6,
            "errors": 5,
            "success_rate": 0.8,
            "coverage_display": "80%",
        }

    @staticmethod
    def summary_from_dict():
        return {
            "trials": 10,
            "tested": 9,
            "found": 8,
            "not_found": 7,
            "timeout": 6,
            "errors": 5,
        }

    def test_serialize(self):
        summary = self.summary_object()
        expected = self.summary_dict()
        assert summary.to_dict() == expected
        assert to_json(summary) == json.dumps(expected)

    def test_deserialize_dict(self):
        expected_dict = self.summary_from_dict()
        assert self.summary_object().from_dict(self.summary_dict()) == expected_dict

    def test_deserialize_json(self):
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

    @staticmethod
    def results_object():
        return TestingResults(
            mutant_trials=[TestMutantTrial.mutant_trial_object()],
            summary=TestTestingSummary.summary_object(),
        )

    @staticmethod
    def results_dict():
        return {
            "mutant_trials": [TestMutantTrial.mutant_trial_dict()],
            "summary": TestTestingSummary.summary_dict(),
        }

    @staticmethod
    def results_from_dict():
        return {
            "mutant_trials": [TestMutantTrial.mutant_trial_object()],
            "summary": TestTestingSummary.summary_object(),
        }

    def test_deserialize_dict(self):
        expected_dict = self.results_from_dict()
        assert self.results_object().from_dict(self.results_dict()) == expected_dict

    def test_deserialize_json(self):
        results = json.dumps(self.results_dict())
        expected = self.results_object()
        assert from_json(results, TestingResults) == expected

    def test_serialize(self):
        results = self.results_object()
        expected = self.results_dict()
        assert results.to_dict() == expected
        assert to_json(results) == json.dumps(expected)

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
