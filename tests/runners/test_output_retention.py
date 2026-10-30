# Copyright (c) 2026 Poodle contributors
"""Retain native command bytes independently of disposable mutation trials."""

import json
import os
import select
import shlex
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock
from zipfile import ZipFile

import click
import pytest

from poodle import PoodleInputError, PoodleNoMutantsFoundError, core, run
from poodle.data_types import Mutant, TestingResults, TestingSummary
from poodle.reporters.basic import report_json
from poodle.runners.command_line import runner
from tests.data_types.test_data import PoodleConfigStub


def invocation(tmp_path, code, **opts):
    source = tmp_path / "source"
    source.mkdir(exist_ok=True)
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    config = PoodleConfigStub(
        source_folders=[source],
        work_folder=work,
        runner="command_line",
        file_flags=0,
        file_filters=[],
        file_copy_flags=0,
        file_copy_filters=[],
        skip_mutators=[],
        add_mutators=[],
        mutator_opts={},
        reporters=[],
        log_format="%(message)s",
        log_level=50,
        echo_enabled=False,
        runner_opts={
            "command_line": shlex.join([sys.executable, "-c", code]),
            "output_dir": str(tmp_path / "evidence"),
            **opts,
        },
        reporter_opts={"json_report_file": str(tmp_path / "report.json"), "json_report_found": True},
    )
    mutant = Mutant("String", 1, 0, 1, 1, "2", Path(), Path("target.py"))
    trial = tmp_path / "trial"
    trial.mkdir(exist_ok=True)
    return config, mutant, trial


def receipt(config):
    records = list(Path(config.runner_opts["output_dir"]).glob("trial-*/trial.json"))
    assert len(records) == 1
    return records[0], json.loads(records[0].read_text())


@pytest.mark.parametrize("exit_code", [0, 1, 2])
def test_every_completed_outcome_keeps_raw_bytes_and_identity(tmp_path, exit_code):
    config, mutant, trial = invocation(
        tmp_path, f"import os; os.write(1,b'out\\xff'); os.write(2,b'err\\xfe'); raise SystemExit({exit_code})"
    )
    result = runner(config, trial, mutant, 5)
    path, metadata = receipt(config)
    assert metadata == {"mutant": mutant.to_dict(), "status": "completed", "return_code": exit_code}
    assert (path.parent / "stdout.txt").read_bytes() == b"out\xff"
    assert (path.parent / "stderr.txt").read_bytes() == b"err\xfe"
    assert result.found is (exit_code != 0)  # #48 changes scoring separately.
    for retained in [path, path.parent / "stdout.txt", path.parent / "stderr.txt"]:
        assert str(retained.resolve()) in result.reason_desc


@pytest.mark.skipif(os.name == "nt", reason="POSIX FIFO synchronization")
def test_bytes_are_visible_before_child_is_released(tmp_path):
    ready, release = tmp_path / "ready", tmp_path / "release"
    os.mkfifo(ready)
    os.mkfifo(release)
    code = (
        "import os; os.write(1,b'live-out'); os.write(2,b'live-err'); "
        f"open({str(ready)!r},'w').write('ready'); open({str(release)!r}).read(1)"
    )
    config, mutant, trial = invocation(tmp_path, code)
    # A ready FIFO read synchronizes with flushed child bytes; no timing sleep.
    ready_fd = os.open(ready, os.O_RDWR | os.O_NONBLOCK)
    release_fd = os.open(release, os.O_RDWR | os.O_NONBLOCK)
    with ThreadPoolExecutor(max_workers=1) as pool:
        result_future = pool.submit(runner, config, trial, mutant, 10)
        try:
            assert select.select([ready_fd], [], [], 5)[0]
            assert os.read(ready_fd, 5) == b"ready"
            directories = list(Path(config.runner_opts["output_dir"]).glob("trial-*"))
            assert len(directories) == 1
            assert (directories[0] / "stdout.txt").read_bytes() == b"live-out"
            assert (directories[0] / "stderr.txt").read_bytes() == b"live-err"
            assert not result_future.done()
        finally:
            os.write(release_fd, b"1")
            try:
                completed = result_future.result(timeout=12)
            finally:
                os.close(release_fd)
                os.close(ready_fd)
        assert completed.found is False


def test_timeout_preserves_partial_output(tmp_path):
    config, mutant, trial = invocation(
        tmp_path, "import os,time; os.write(1,b'partial-out'); os.write(2,b'partial-err'); time.sleep(30)"
    )
    result = runner(config, trial, mutant, 2)
    path, metadata = receipt(config)
    assert metadata["status"] == "timeout"
    assert metadata["return_code"] is None
    assert (path.parent / "stdout.txt").read_bytes() == b"partial-out"
    assert (path.parent / "stderr.txt").read_bytes() == b"partial-err"
    assert "TimeoutExpired" in result.reason_desc


@pytest.mark.skipif(os.name == "nt", reason="POSIX negative subprocess signal return codes")
def test_signal_receipt_keeps_actual_negative_returncode(tmp_path):
    config, mutant, trial = invocation(
        tmp_path, f"import os; os.write(1,b'before-signal'); os.kill(os.getpid(),{signal.SIGTERM})"
    )
    runner(config, trial, mutant, 5)
    path, metadata = receipt(config)
    assert metadata["status"] == "completed"
    assert metadata["return_code"] == -signal.SIGTERM
    assert (path.parent / "stdout.txt").read_bytes() == b"before-signal"


def test_identical_concurrent_trials_never_overwrite(tmp_path):
    config, mutant, trial = invocation(tmp_path, "print('same')")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: runner(config, trial, mutant, 5), range(2)))
    assert all(not result.found for result in results)
    records = list(Path(config.runner_opts["output_dir"]).glob("trial-*/trial.json"))
    assert len(records) == 2
    assert all((path.parent / "stdout.txt").read_bytes() == b"same\n" for path in records)


@pytest.mark.parametrize("error", [OSError("launch refused"), KeyboardInterrupt()])
def test_exception_receipts_survive_without_swallowing_exception(tmp_path, error):
    config, mutant, trial = invocation(tmp_path, "pass")
    with mock.patch("subprocess.run", side_effect=error), pytest.raises(type(error)):
        runner(config, trial, mutant, 5)
    _, metadata = receipt(config)
    assert metadata["status"] == ("interrupted" if isinstance(error, KeyboardInterrupt) else "launch_error")
    assert metadata["return_code"] is None


@pytest.mark.parametrize("location", ["work", "inside_work", "source"])
def test_direct_runner_refuses_disposable_or_copied_output_roots(tmp_path, location):
    config, mutant, trial = invocation(tmp_path, "raise SystemExit('must not launch')")
    root = {
        "work": config.work_folder,
        "inside_work": config.work_folder / "evidence",
        "source": config.source_folders[0],
    }[location]
    config.runner_opts["output_dir"] = root
    with pytest.raises(PoodleInputError):
        runner(config, trial, mutant, 5)


def test_native_core_refuses_before_deleting_retained_evidence(tmp_path):
    config, _, _ = invocation(tmp_path, "pass")
    root = config.work_folder / "retained"
    root.mkdir()
    sentinel = root / "prior-result"
    sentinel.write_text("keep")
    config.runner_opts["output_dir"] = root
    raised = None
    try:
        core.main_process(config)
    except (PoodleInputError, PoodleNoMutantsFoundError) as error:
        raised = error
    assert sentinel.exists(), "native core deleted retained evidence before validating output_dir"
    assert sentinel.read_text() == "keep"
    assert isinstance(raised, PoodleInputError)


def test_native_trial_cleanup_keeps_output_and_existing_json_links(tmp_path, monkeypatch):
    config, mutant, _ = invocation(tmp_path, "print('retained')")
    monkeypatch.chdir(config.source_folders[0])
    original = Path("target.py")
    original.write_text("1\n")
    archive = tmp_path / "source.zip"
    with ZipFile(archive, "w") as zipped:
        zipped.write(original)
    result = run.run_mutant_trial(config, click.secho, archive, mutant, "retained", runner, 5)
    assert not (config.work_folder / "run-retained").exists()
    assert original.read_text() == "1\n"
    path, _ = receipt(config)
    summary = TestingSummary(trials=1)
    summary += result.result
    report_json(config, click.secho, TestingResults([result], summary))
    body = json.loads((tmp_path / "report.json").read_text())
    assert str(path.resolve()) in body["mutant_trials"][0]["result"]["reason_desc"]
    assert (path.parent / "stdout.txt").read_bytes() == b"retained\n"


def test_disabled_retention_preserves_existing_command_behavior(tmp_path):
    config, mutant, trial = invocation(tmp_path, "print('ordinary')")
    del config.runner_opts["output_dir"]
    result = runner(config, trial, mutant, 5)
    assert result.found is False
    assert result.reason_desc is None
    assert not (tmp_path / "evidence").exists()
