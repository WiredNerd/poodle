from concurrent.futures import Future
from pathlib import Path
from unittest import mock

import click
import pytest

from poodle import run
from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, PoodleWork, TestingResults, TestingSummary
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.run.logger") as logger:
        yield logger


@pytest.fixture()
def mock_echo():
    return mock.MagicMock()


@pytest.fixture()
def mock_time():
    with mock.patch("poodle.run.time") as time:
        yield time


def test_logger():
    assert run.logger.name == "poodle.run"


def test_builtin_runners():
    assert run.builtin_runners == {
        "command_line": run.command_line.runner,
    }


class TestGetRunner:
    def test_builtin_runner(self, mock_logger):
        config = PoodleConfigStub(runner="command_line")
        assert run.get_runner(config) is run.command_line.runner
        mock_logger.debug.assert_called_with("Runner: %s", config.runner)

    def test_external_runner(self, mock_logger):
        config = PoodleConfigStub(runner="poodle.runners.command_line.runner")
        assert run.get_runner(config) is run.command_line.runner
        mock_logger.debug.assert_called_with("Runner: %s", config.runner)

    def test_external_runner_not_found(self, mock_logger):
        config = PoodleConfigStub(runner="poodle.runners.not_found.runner")
        with pytest.raises(ImportError):
            run.get_runner(config)
        mock_logger.debug.assert_called_with("Runner: %s", config.runner)


class TestCleanRunTrial:
    @mock.patch("poodle.run.clean_run_trial")
    def test_clean_run_each_source_folder(self, clean_run_trial):
        clean_run_trial.side_effect = [1, 2, 3]
        folder_1 = Path("folder_1")
        folder_2 = Path("folder_2")
        folder_3 = Path("folder_3")

        work = PoodleWork(config=PoodleConfigStub(source_folders=[folder_1, folder_2, folder_3]))
        assert run.clean_run_each_source_folder(work) == {
            folder_1: 1,
            folder_2: 2,
            folder_3: 3,
        }

    @mock.patch("poodle.run.run_mutant_trial")
    def test_clean_run_trial(self, run_mutant_trial, mock_logger, mock_echo, mock_time):
        mock_time.time.side_effect = [1, 3]

        folder = Path("source_folder")

        work = PoodleWork(config=PoodleConfigStub())
        work.echo = mock_echo
        work.folder_zips = {folder: Path("folder.zip")}

        mutant = Mutant(
            mutator_name="",
            source_folder=folder,
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        )

        trial = MutantTrial(mutant, MutantTrialResult(False, MutantTrialResult.RC_NOT_FOUND), 1)

        run_mutant_trial.return_value = trial

        assert run.clean_run_trial(work, folder) == trial

        assert run_mutant_trial.call_args.kwargs["config"] == work.config
        assert run_mutant_trial.call_args.kwargs["echo"] == mock_echo
        assert run_mutant_trial.call_args.kwargs["folder_zip"] == Path("folder.zip")
        assert run_mutant_trial.call_args.kwargs["mutant"] == mutant
        assert run_mutant_trial.call_args.kwargs["run_id"] == "1"
        assert run_mutant_trial.call_args.kwargs["runner"] == work.runner
        assert run_mutant_trial.call_args.kwargs["timeout"] is None

        mock_echo.assert_any_call(f"Testing clean run of folder '{folder}'...", nl=False)
        mock_echo.assert_any_call("PASSED")

        mock_logger.info.assert_called_with("Elapsed Time %.2f s", 2)

    @mock.patch("poodle.run.run_mutant_trial")
    def test_clean_run_trial_failed(self, run_mutant_trial, mock_echo):
        folder = Path("source_folder")

        work = PoodleWork(config=PoodleConfigStub())
        work.echo = mock_echo
        work.folder_zips = {folder: Path("folder.zip")}

        mutant = Mutant(
            mutator_name="",
            source_folder=folder,
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        )

        trial = MutantTrial(mutant, MutantTrialResult(True, MutantTrialResult.RC_FOUND), 1)

        run_mutant_trial.return_value = trial

        with pytest.raises(run.PoodleTrialRunError) as err:  # noqa: PT012
            run.clean_run_trial(work, folder)
            assert err.value.args[0] == "Clean Run Failed"
            assert err.value.args[1] == MutantTrialResult.RC_FOUND

        mock_echo.assert_any_call(f"Testing clean run of folder '{folder}'...", nl=False)
        mock_echo.assert_any_call(click.style("FAILED", fg="red"))


class TestMutantTrials:
    def create_mutant(self, folder, text):
        return Mutant(
            mutator_name="",
            source_folder=folder,
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text=text,
        )

    @mock.patch("poodle.run.concurrent")
    def test_run_mutant_trails(self, concurrent, mock_logger, mock_echo, mock_time):
        mock_time.time.side_effect = [1, 3]

        folder = Path("source_folder")

        work = PoodleWork(config=PoodleConfigStub(max_workers=10))
        work.echo = mock_echo
        work.folder_zips = {folder: Path("folder.zip")}

        mutants = [
            self.create_mutant(folder, "mut1"),
            self.create_mutant(folder, "mut2"),
        ]

        trials = [
            MutantTrial(mutants[0], MutantTrialResult(False, MutantTrialResult.RC_NOT_FOUND), 1),
            MutantTrial(mutants[1], MutantTrialResult(True, MutantTrialResult.RC_FOUND), 1),
        ]

        futures = [mock.MagicMock(spec=Future) for _ in trials]
        for i, trial in enumerate(trials):
            futures[i].result.return_value = trial
            futures[i].cancelled.return_value = False
        concurrent.futures.as_completed.return_value = futures

        executor = concurrent.futures.ProcessPoolExecutor.return_value.__enter__.return_value
        executor.submit.side_effect = futures

        summary = TestingSummary(trials=2, tested=2, found=1, not_found=1)
        testing_results = TestingResults(mutant_trials=trials, summary=summary)

        actual_results = run.run_mutant_trails(work, mutants, 10)

        mock_echo.assert_any_call("Testing mutants")

        concurrent.futures.ProcessPoolExecutor.assert_called_with(max_workers=work.config.max_workers)

        for i, mutant in enumerate(mutants):
            executor.submit.assert_any_call(
                run.run_mutant_trial,
                work.config,
                mock_echo,
                Path("folder.zip"),
                mutant,
                str(i + 1),
                work.runner,
                10,
            )

        mock_echo.assert_any_call("COMPLETED    1/2   \tFOUND    0\tNOT FOUND    1\tTIMEOUT    0\tERRORS    0")
        mock_echo.assert_any_call("COMPLETED    2/2   \tFOUND    1\tNOT FOUND    1\tTIMEOUT    0\tERRORS    0")

        mock_logger.info.assert_called_with("Elapsed Time %.2f s", 2)

        assert actual_results == testing_results

    @mock.patch("poodle.run.concurrent")
    def test_run_mutant_trails_cancelled(self, concurrent, mock_echo, mock_time):
        mock_time.time.side_effect = [1, 3]

        folder = Path("source_folder")

        work = PoodleWork(config=PoodleConfigStub())
        work.echo = mock_echo
        work.folder_zips = {folder: Path("folder.zip")}

        mutants = [
            self.create_mutant(folder, "mut1"),
            self.create_mutant(folder, "mut2"),
        ]

        trials = [
            MutantTrial(mutants[0], MutantTrialResult(False, MutantTrialResult.RC_NOT_FOUND), 1),
            MutantTrial(mutants[1], MutantTrialResult(True, MutantTrialResult.RC_FOUND), 1),
        ]

        futures = [mock.MagicMock(spec=Future) for _ in trials]
        for i, trial in enumerate(trials):
            futures[i].result.return_value = trial
            futures[i].cancelled.return_value = True
        concurrent.futures.as_completed.return_value = futures

        executor = concurrent.futures.ProcessPoolExecutor.return_value.__enter__.return_value
        executor.submit.side_effect = futures

        summary = TestingSummary(trials=2, tested=0, found=0, not_found=0)
        testing_results = TestingResults(mutant_trials=trials, summary=summary)

        actual_results = run.run_mutant_trails(work, mutants, 10)

        mock_echo.assert_has_calls(
            [
                mock.call("Testing mutants"),
                mock.call("Canceled"),
                mock.call("Canceled"),
            ]
        )

        assert actual_results == testing_results

    @mock.patch("poodle.run.concurrent")
    def test_run_mutant_trails_interrupt(self, concurrent, mock_echo):
        folder = Path("source_folder")

        work = PoodleWork(config=PoodleConfigStub())
        work.echo = mock_echo
        work.folder_zips = {folder: Path("folder.zip")}

        mutants = [
            self.create_mutant(folder, "mut1"),
            self.create_mutant(folder, "mut2"),
        ]

        executor = concurrent.futures.ProcessPoolExecutor.return_value.__enter__.return_value
        executor.submit.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            run.run_mutant_trails(work, mutants, 10)

        mock_echo.assert_has_calls(
            [
                mock.call("Testing mutants"),
                mock.call("Received Keyboard Interrupt.  Cancelling Remaining Trials."),
            ]
        )

        executor.shutdown.assert_called_with(wait=True, cancel_futures=True)


class TestRunMutantTrial:
    def create_mutant(self, folder, source_file):
        return Mutant(
            mutator_name="",
            source_folder=folder,
            source_file=source_file,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        )

    @mock.patch("poodle.run.logging")
    @mock.patch("poodle.run.ZipFile")
    @mock.patch("poodle.run.mutate_lines")
    @mock.patch("poodle.run.shutil")
    def test_run_mutant_trial(
        self,
        mock_shutil,
        mutate_lines,
        zip_file_cls,
        mock_logging,
        mock_logger,
        mock_echo,
        mock_time,
    ):
        mock_time.time.side_effect = [1, 3]
        mock_work_folder = mock.MagicMock(spec=Path)
        config = PoodleConfigStub(work_folder=mock_work_folder, log_format="log_format", log_level="DEBUG")
        runner = mock.MagicMock()
        folder = Path("folder")
        mutant = self.create_mutant(folder, Path("main.py"))

        run_folder = config.work_folder.__truediv__.return_value
        target_file = run_folder.__truediv__.return_value
        file_lines_orig = target_file.read_text.return_value.splitlines.return_value
        mutate_lines.return_value = ["line1\n", "line2\n"]

        result = runner.return_value

        returned_trial = run.run_mutant_trial(config, mock_echo, Path("folder.zip"), mutant, "1", runner, 10)

        mock_logging.basicConfig.assert_called_with(format=config.log_format, level=config.log_level)

        mock_logger.debug.assert_any_call(
            "SETUP: run_id=%s folder_zip=%s file=%s:%s text='%s'",
            "1",
            Path("folder.zip"),
            Path("main.py"),
            0,
            "",
        )

        config.work_folder.__truediv__.assert_called_with("run-1")
        run_folder.mkdir.assert_called_with()

        zip_file_cls.assert_called_with(Path("folder.zip"), "r")
        zip_file = zip_file_cls.return_value.__enter__.return_value
        zip_file.extractall.assert_called_with(run_folder)

        target_file.read_text.assert_called_with("utf-8")
        target_file.read_text.return_value.splitlines.assert_called_with(keepends=True)
        mutate_lines.assert_called_with(mutant, file_lines_orig)
        target_file.write_text.assert_called_with(data="line1\nline2\n", encoding="utf-8")

        mock_logger.debug.assert_any_call("START: run_id=%s run_folder=%s", "1", run_folder)

        runner.assert_called_with(
            config=config,
            echo=mock_echo,
            run_folder=run_folder,
            mutant=mutant,
            timeout=10,
        )

        mock_shutil.rmtree.assert_called_with(run_folder)

        mock_logger.debug.assert_any_call("END: run_id=%s - Elapsed Time %.2f s", "1", 2)

        assert returned_trial == MutantTrial(mutant, result, 2)

    @mock.patch("poodle.run.logging")
    @mock.patch("poodle.run.ZipFile")
    @mock.patch("poodle.run.mutate_lines")
    @mock.patch("poodle.run.shutil")
    def test_run_mutant_trial_no_source(
        self,
        mock_shutil,
        mutate_lines,
        zip_file_cls,
        mock_logging,
        mock_logger,
        mock_echo,
        mock_time,
    ):
        mock_time.time.side_effect = [1, 3]
        mock_work_folder = mock.MagicMock(spec=Path)
        config = PoodleConfigStub(work_folder=mock_work_folder, log_format="log_format", log_level="DEBUG")
        runner = mock.MagicMock()
        folder = Path("folder")
        mutant = self.create_mutant(folder, None)

        run_folder = config.work_folder.__truediv__.return_value
        target_file = run_folder.__truediv__.return_value

        result = runner.return_value

        returned_trial = run.run_mutant_trial(config, mock_echo, Path("folder.zip"), mutant, "1", runner, 10)

        mock_logging.basicConfig.assert_called_with(format=config.log_format, level=config.log_level)

        mock_logger.debug.assert_any_call(
            "SETUP: run_id=%s folder_zip=%s file=%s:%s text='%s'",
            "1",
            Path("folder.zip"),
            None,
            0,
            "",
        )

        config.work_folder.__truediv__.assert_called_with("run-1")
        run_folder.mkdir.assert_called_with()

        zip_file_cls.assert_called_with(Path("folder.zip"), "r")
        zip_file = zip_file_cls.return_value.__enter__.return_value
        zip_file.extractall.assert_called_with(run_folder)

        run_folder.__truediv__.assert_not_called()
        target_file.read_text.assert_not_called()
        mutate_lines.assert_not_called()
        target_file.write_text.assert_not_called()

        mock_logger.debug.assert_any_call("START: run_id=%s run_folder=%s", "1", run_folder)

        runner.assert_called_with(
            config=config,
            echo=mock_echo,
            run_folder=run_folder,
            mutant=mutant,
            timeout=10,
        )

        mock_shutil.rmtree.assert_called_with(run_folder)

        mock_logger.debug.assert_any_call("END: run_id=%s - Elapsed Time %.2f s", "1", 2)

        assert returned_trial == MutantTrial(mutant, result, 2)
