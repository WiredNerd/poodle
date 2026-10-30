"""Exercise command outcomes through reporting without treating errors as kills."""

import json
import os
import shlex
import signal
import sys
from pathlib import Path

import click
import pytest

from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, TestingResults, TestingSummary
from poodle.reporters.basic import report_json
from poodle.runners.command_line import runner
from tests.data_types.test_data import PoodleConfigStub


def run_command(tmp_path, code, timeout=5):
    command = shlex.join([sys.executable, "-c", code])
    config = PoodleConfigStub(
        runner_opts={"command_line": command},
        reporter_opts={"json_report_file": str(tmp_path / "results.json")},
    )
    mutant = Mutant("example", 1, 0, 1, 1, "0", Path("src"), Path("example.py"))
    result = runner(config, tmp_path, mutant, timeout)
    summary = TestingSummary(trials=1)
    summary += result
    report_json(config, click.secho, TestingResults([MutantTrial(mutant, result, 0.0)], summary))
    report = json.loads((tmp_path / "results.json").read_text())
    return result, summary, report


@pytest.mark.parametrize("exit_code", [0, 1, 2, 3, 4, 5])
def test_command_exit_classification_reaches_summary_and_default_json(tmp_path, exit_code):
    result, summary, report = run_command(
        tmp_path,
        f"import sys; print('retained stdout'); print('retained stderr', file=sys.stderr); sys.exit({exit_code})",
    )
    if exit_code == 1:
        assert result.found is True
        assert result.reason_code == MutantTrialResult.RC_FOUND
        assert (summary.found, summary.not_found, summary.errors) == (1, 0, 0)
        assert report["mutant_trials"] == []  # Default reporting omits successful detections.
    elif exit_code == 0:
        assert result.found is False
        assert result.reason_code == MutantTrialResult.RC_NOT_FOUND
        assert (summary.found, summary.not_found, summary.errors) == (0, 1, 0)
        assert len(report["mutant_trials"]) == 1
    else:
        assert result.found is False
        assert result.reason_code == MutantTrialResult.RC_OTHER
        assert "retained stdout" in result.reason_desc
        assert "retained stderr" in result.reason_desc
        assert (summary.found, summary.not_found, summary.errors) == (0, 0, 1)
        assert summary.success_rate == 0
        assert report["summary"]["errors"] == 1
        assert report["mutant_trials"][0]["result"]["reason_code"] == MutantTrialResult.RC_OTHER


@pytest.mark.skipif(os.name == "nt", reason="POSIX subprocess signal return codes")
def test_signal_termination_is_an_error_visible_in_default_report(tmp_path):
    result, summary, report = run_command(tmp_path, f"import os; os.kill(os.getpid(), {signal.SIGTERM})")
    assert result.found is False
    assert result.reason_code == MutantTrialResult.RC_OTHER
    assert (summary.found, summary.errors) == (0, 1)
    assert report["mutant_trials"][0]["result"]["reason_code"] == MutantTrialResult.RC_OTHER


def test_timeout_remains_distinct_from_errors_and_survivors(tmp_path):
    result, summary, report = run_command(tmp_path, "import time; time.sleep(5)", timeout=0.1)
    assert result.found is False
    assert result.reason_code == MutantTrialResult.RC_TIMEOUT
    assert (summary.found, summary.not_found, summary.timeout, summary.errors) == (0, 0, 1, 0)
    assert report["mutant_trials"][0]["result"]["reason_code"] == MutantTrialResult.RC_TIMEOUT


def test_legacy_operational_receipt_cannot_inflate_kill_summary():
    summary = TestingSummary(trials=1)
    summary += MutantTrialResult(found=True, reason_code=MutantTrialResult.RC_OTHER)
    assert (summary.found, summary.not_found, summary.errors) == (0, 0, 1)
    assert summary.success_rate == 0


def test_custom_runner_found_reason_stays_supported():
    summary = TestingSummary(trials=1)
    summary += MutantTrialResult(found=True, reason_code="Custom runner detection")
    assert (summary.found, summary.errors) == (1, 0)
