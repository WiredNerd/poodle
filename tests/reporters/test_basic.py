from __future__ import annotations

from pathlib import Path
from unittest import mock

import click
import pytest

from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, TestingResults, TestingSummary
from poodle.reporters import report_not_found, report_summary
from tests.data_types.test_data import PoodleConfigStub


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
                mock.call("!!! No mutants found to test !!!", fg="yellow"),
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
                mock.call("*** Results Summary ***", fg="green"),
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
                mock.call("*** Results Summary ***", fg="green"),
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
                mock.call("*** Results Summary ***", fg="green"),
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
                mock.call("*** Results Summary ***", fg="green"),
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
                mock.call("*** Results Summary ***", fg="green"),
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
        passed=False,
        reason_code=MutantTrialResult.RC_NOT_FOUND,
        reason_desc=None,
        duration=1.0,
        unified_diff=None,
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
                unified_diff=unified_diff,
            ),
            result=MutantTrialResult(
                passed=passed,
                reason_code=reason_code,
                reason_desc=reason_desc,
            ),
            duration=duration,
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
        report_not_found(config=PoodleConfigStub(), echo=mock_echo, testing_results=results)
        mock_echo.assert_not_called()

    @pytest.mark.parametrize(
        ("reporter_opts", "file"),
        [
            ({}, None),
            ({"not_found_file": "outfile.txt"}, "outfile.txt"),
        ],
    )
    def test_failed(self, reporter_opts, file, mock_echo: mock.MagicMock):
        source_file = mock.MagicMock()
        source_file.read_text.return_value.splitlines.return_value = ["lambda x: x + 1\n"]
        source_file.resolve.return_value = "src/example.py"
        source_file.__str__.return_value = "example.py"  # type: ignore [attr-defined]

        diff_str = (
            "--- src/example.py\n"
            "+++ [Mutant] src/example.py:1\n"
            "@@ -1 +1 @@\n"
            "-lambda x: x + 1\n"
            "+lambda x: None\n"
        )

        results = TestingResults(
            mutant_trials=[
                self.create_trial(
                    mutator_name="NotFound",
                    source=source_file,
                    unified_diff=diff_str,
                ),
                self.create_trial(
                    mutator_name="ReasonDesc",
                    source=source_file,
                    reason_code=MutantTrialResult.RC_OTHER,
                    reason_desc="error message",
                    unified_diff=diff_str,
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
        report_not_found(
            config=PoodleConfigStub(reporter_opts=reporter_opts),
            echo=mock_echo,
            testing_results=results,
        )

        mock_echo.assert_has_calls(
            [
                mock.call("", file=file),
                mock.call("*** Mutants Not Found ***", fg="yellow", file=file),
                mock.call("", file=file),
                mock.call("Mutant Trial Result: Mutant Not Found", file=file),
                mock.call("Mutator: NoSource", file=file),
                mock.call("source_file=None lineno=1 col_offset=10 end_lineno=1 end_col_offset=15", file=file),
                mock.call("text:", file=file),
                mock.call("None", file=file),
                mock.call("", file=file),
                mock.call("Mutant Trial Result: Mutant Not Found", file=file),
                mock.call("Mutator: NotFound", file=file),
                mock.call(diff_str, file=file),
                mock.call("", file=file),
                mock.call("Mutant Trial Result: other", file=file),
                mock.call("Mutator: ReasonDesc", file=file),
                mock.call("error message", file=file),
                mock.call(diff_str, file=file),
            ]
        )
