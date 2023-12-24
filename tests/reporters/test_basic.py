from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from poodle import util
from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, TestingResults, TestingSummary
from poodle.reporters import basic, report_not_found, report_summary
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


def create_trial(
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
            found=passed,
            reason_code=reason_code,
            reason_desc=reason_desc,
        ),
        duration=duration,
    )


class TestGetIncludeStatuses:
    @pytest.mark.parametrize(
        ("report_found", "report_not_found", "expected"),
        [
            (None, None, {False}),
            (False, None, {False}),
            (True, None, {True, False}),
            (None, False, set()),
            (None, True, {False}),
            (True, True, {True, False}),
            (True, False, {True}),
            (False, False, set()),
            (False, True, {False}),
        ],
    )
    def test_get_include_statuses(self, report_found, report_not_found, expected):
        prefix = "example"
        reporter_opts = {}
        if report_found is not None:
            reporter_opts[f"{prefix}_report_found"] = report_found
        if report_not_found is not None:
            reporter_opts[f"{prefix}_report_not_found"] = report_not_found

        config = PoodleConfigStub(reporter_opts=reporter_opts)
        assert basic.get_include_statuses(config, prefix) == expected


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
            summary=TestingSummary(trials=10, found=10),
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
            summary=TestingSummary(trials=9, found=6, not_found=2),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call(""),
                mock.call("*** Results Summary ***", fg="green"),
                mock.call("Testing found 66.7% of Mutants."),
                mock.call(" - 2 mutant(s) were not found."),
            ]
        )

    def test_timeout(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=9, found=3, timeout=2),
        )
        report_summary(mock_echo, results)

        mock_echo.assert_has_calls(
            [
                mock.call(""),
                mock.call("*** Results Summary ***", fg="green"),
                mock.call("Testing found 33.3% of Mutants."),
                mock.call(" - 2 mutant(s) caused trial to timeout."),
            ]
        )

    def test_errors(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[],
            summary=TestingSummary(trials=10, found=8, errors=2),
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
            summary=TestingSummary(trials=10, found=4, not_found=2, timeout=2, errors=2),
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
    def test_all_passed(self, mock_echo: mock.MagicMock):
        results = TestingResults(
            mutant_trials=[
                create_trial(passed=True),
                create_trial(passed=True),
                create_trial(passed=True),
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
                create_trial(
                    mutator_name="NotFound",
                    source=source_file,
                    unified_diff=diff_str,
                ),
                create_trial(
                    mutator_name="ReasonDesc",
                    source=source_file,
                    reason_code=MutantTrialResult.RC_OTHER,
                    reason_desc="error message",
                    unified_diff=diff_str,
                ),
                create_trial(
                    mutator_name="Passed",
                    passed=True,
                ),
                create_trial(
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
                mock.call("Mutant Trial Result: Other, See Description", file=file),
                mock.call("Mutator: ReasonDesc", file=file),
                mock.call("error message", file=file),
                mock.call(diff_str, file=file),
            ]
        )


class TestReportJson:
    @pytest.fixture()
    def mock_path(self):
        with mock.patch("poodle.reporters.basic.Path") as mock_path:
            yield mock_path

    def test_all_passed(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(passed=True),
                create_trial(passed=True),
                create_trial(passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=[],
                summary=results.summary,
            )
        )
        mock_path.assert_called_once_with("mutation-testing-report.json")
        mock_path.return_value.write_text.assert_called_once_with(expected)
        mock_echo.assert_called_once_with("JSON report written to mutation-testing-report.json", fg="green")

    def test_failed(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(lineno=1, passed=True),
                create_trial(lineno=2, passed=False),
                create_trial(lineno=3, passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=[
                    create_trial(lineno=2, passed=False),
                ],
                summary=results.summary,
            )
        )
        mock_path.return_value.write_text.assert_called_once_with(expected)

    def test_include_all(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(lineno=1, passed=True),
                create_trial(lineno=2, passed=False),
                create_trial(lineno=3, passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={"json_report_found": True}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=results.mutant_trials,
                summary=results.summary,
            )
        )
        mock_path.return_value.write_text.assert_called_once_with(expected)

    def test_no_summary(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(lineno=1, passed=True),
                create_trial(lineno=2, passed=False),
                create_trial(lineno=3, passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={"json_include_summary": False}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=[
                    create_trial(lineno=2, passed=False),
                ],
                summary=None,
            )
        )
        mock_path.return_value.write_text.assert_called_once_with(expected)

    def test_file_name(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(lineno=1, passed=True),
                create_trial(lineno=2, passed=False),
                create_trial(lineno=3, passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={"json_report_file": Path("outfile.json")}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=[
                    create_trial(lineno=2, passed=False),
                ],
                summary=results.summary,
            )
        )
        mock_path.assert_called_once_with(Path("outfile.json"))
        mock_path.return_value.write_text.assert_called_once_with(expected)
        mock_echo.assert_called_once_with("JSON report written to outfile.json", fg="green")

    def test_sysout(self, mock_echo, mock_path):
        results = TestingResults(
            mutant_trials=[
                create_trial(lineno=1, passed=True),
                create_trial(lineno=2, passed=False),
                create_trial(lineno=3, passed=True),
            ],
            summary=TestingSummary(),
        )
        basic.report_json(
            config=PoodleConfigStub(reporter_opts={"json_report_file": "sysout"}),
            echo=mock_echo,
            testing_results=results,
        )

        expected = util.to_json(
            TestingResults(
                mutant_trials=[
                    create_trial(lineno=2, passed=False),
                ],
                summary=results.summary,
            ),
            indent=4,
        )
        mock_path.assert_not_called()
        mock_echo.assert_has_calls(
            [
                mock.call(expected),
                mock.call("JSON report written to sysout", fg="green"),
            ]
        )
