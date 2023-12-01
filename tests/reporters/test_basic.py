from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, TestingResults, TestingSummary
from poodle.reporters import report_not_found, report_summary


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


class TestReportSummary:
    def test_no_mutants(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=0),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("No mutants found to test."),
            ]
        )

    def test_all_found(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=10, success_rate=1.0),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("*** Results Summary ***"),
                mock.call("Testing found 100.0% of Mutants."),
            ]
        )

    def test_not_found(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=8, not_found=2, success_rate=0.8888),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("*** Results Summary ***"),
                mock.call("Testing found 88.9% of Mutants."),
                mock.call(" - 2 mutant(s) were not found."),
            ]
        )

    def test_timeout(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=8, timeout=2, success_rate=0.4444),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("*** Results Summary ***"),
                mock.call("Testing found 44.4% of Mutants."),
                mock.call(" - 2 mutant(s) caused trial to timeout."),
            ]
        )

    def test_errors(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=8, errors=2, success_rate=0.8),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("*** Results Summary ***"),
                mock.call("Testing found 80.0% of Mutants."),
                mock.call(" - 2 mutant(s) could not be tested due to an error."),
            ]
        )

    def test_all(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=4, not_found=2, timeout=2, errors=2, success_rate=0.4),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call("*** Results Summary ***"),
                mock.call("Testing found 40.0% of Mutants."),
                mock.call(" - 2 mutant(s) were not found."),
                mock.call(" - 2 mutant(s) caused trial to timeout."),
                mock.call(" - 2 mutant(s) could not be tested due to an error."),
            ]
        )


class TestReportNotFound:
    def create_trial(
        self,
        lineno=1,
        source="example.py",
        text="None",
        passed=False,  # noqa: FBT002
        reason_code="mutant_not_found",
        reason_desc=None,
    ):
        return MutantTrial(
            mutant=Mutant(
                mutator_name="TestMutator",
                lineno=lineno,
                col_offset=0,
                end_lineno=1,
                end_col_offset=10,
                text=text,
                source_folder=Path(),
                source_file=Path(source) if source is not None else None,
            ),
            result=MutantTrialResult(
                passed=passed,
                reason_code=reason_code,
                reason_desc=reason_desc,
            ),
        )

    def test_all_passed(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[
                self.create_trial(passed=True),
                self.create_trial(passed=True),
                self.create_trial(passed=True),
            ],
            summary=TestingSummary(),
        )
        report_not_found(mock_echo, results)
        mock_echo.assert_not_called()

    def test_failed(self, mock_echo: mock.MagicMock):
        source_str = str(Path("example.py").resolve())
        results = TestingResults(
            mutant_trials=[
                self.create_trial(),
                self.create_trial(
                    lineno=2,
                    text="continue",
                    reason_code="mutant_other",
                    reason_desc="error message",
                ),
                self.create_trial(passed=True),
                self.create_trial(source=None),
            ],
            summary=TestingSummary(),
        )
        report_not_found(mock_echo, results)
        mock_echo.assert_has_calls(
            [
                mock.call("\nMutants Not Found:"),
                mock.call(f"Mutant: {source_str}:1"),
                mock.call("None"),
                mock.call("Result: mutant_not_found"),
                mock.call(""),
                mock.call(f"Mutant: {source_str}:2"),
                mock.call("continue"),
                mock.call("Result: mutant_other"),
                mock.call("error message"),
                mock.call(""),
                mock.call("Mutant: None:1"),
                mock.call("None"),
                mock.call("Result: mutant_not_found"),
                mock.call(""),
            ]
        )
