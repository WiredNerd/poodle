from __future__ import annotations

from pathlib import Path
from unittest import mock

import click
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
                mock.call(""),
                mock.call(click.style("!!! No mutants found to test !!!", fg="yellow")),
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
                mock.call(""),
                mock.call(click.style("*** Results Summary ***", fg="green")),
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
                mock.call(""),
                mock.call(click.style("*** Results Summary ***", fg="green")),
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
                mock.call(""),
                mock.call(click.style("*** Results Summary ***", fg="green")),
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
                mock.call(""),
                mock.call(click.style("*** Results Summary ***", fg="green")),
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
                mock.call(""),
                mock.call(click.style("*** Results Summary ***", fg="green")),
                mock.call("Testing found 40.0% of Mutants."),
                mock.call(" - 2 mutant(s) were not found."),
                mock.call(" - 2 mutant(s) caused trial to timeout."),
                mock.call(" - 2 mutant(s) could not be tested due to an error."),
            ]
        )


class TestReportNotFound:
    def create_trial(
        self,
        mutator_name="TestMutator",
        source="example.py",
        lineno=1,
        col_offset=10,
        end_lineno=1,
        end_col_offset=15,
        text="None",
        passed=False,  # noqa: FBT002
        reason_code=MutantTrialResult.RC_NOT_FOUND,
        reason_desc=None,
    ):
        source_file = None
        if isinstance(source, str):
            source_file = Path(source)
        elif source:
            source_file = source
        return MutantTrial(
            mutant=Mutant(
                mutator_name=mutator_name,
                lineno=lineno,
                col_offset=col_offset,
                end_lineno=end_lineno,
                end_col_offset=end_col_offset,
                text=text,
                source_folder=Path(),
                source_file=source_file,
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
        source_file = mock.MagicMock()
        source_file.read_text.return_value.splitlines.return_value = ["lambda x: x + 1\n"]
        source_file.resolve.return_value = "src/example.py"
        source_file.__str__.return_value = "example.py"  # type: ignore [attr-defined]

        results = TestingResults(
            mutant_trials=[
                self.create_trial(
                    mutator_name="NotFound",
                    source=source_file,
                ),
                self.create_trial(
                    mutator_name="ReasonDesc",
                    source=source_file,
                    reason_code=MutantTrialResult.RC_OTHER,
                    reason_desc="error message",
                ),
                self.create_trial(
                    mutator_name="Passed",
                    passed=True,
                ),
                self.create_trial(
                    mutator_name="NoSource",
                    source=None,
                ),
            ],
            summary=TestingSummary(),
        )
        report_not_found(mock_echo, results)
        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py\n"
            "@@ -1 +1 @@\n"
            "-lambda x: x + 1\n"
            "+lambda x: None\n"
        )
        expected_report = [
            "",
            click.style("*** Mutants Not Found ***", fg="yellow"),
            "",
            "Mutant Trial Result: Mutant Not Found",
            "Mutator: NotFound",
            diff_str,
            "",
            "Mutant Trial Result: other",
            "Mutator: ReasonDesc",
            "error message",
            diff_str,
            "",
            "Mutant Trial Result: Mutant Not Found",
            "Mutator: NoSource",
            "source_file=None lineno=1 col_offset=10 end_lineno=1 end_col_offset=15",
            "text:",
            "None",
        ]
        actual_report = [args[0][0] for args in mock_echo.call_args_list]
        assert expected_report == actual_report

        source_file.read_text.assert_called_with("utf-8")
        source_file.read_text.return_value.splitlines.assert_called_with(keepends=True)
