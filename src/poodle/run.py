"""Run Mutation Trials."""

from __future__ import annotations

import concurrent.futures
import logging
import math
import time
from typing import TYPE_CHECKING, Callable
from zipfile import ZipFile

import dill
import pluggy
from click import style

from .common.config import PoodleConfigData
from .common.data import (
    CleanRunTrial,
    Mutant,
    MutantTrial,
    MutantTrialResult,
    RunResult,
    TestingResults,
    TestingSummary,
)
from .common.echo_wrapper import EchoWrapper
from .common.exceptions import PoodleTrialRunError
from .common.file_utils import delete_folder
from .common.util import mutate_lines

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def clean_run_each_source_folder(
    folder_zips: dict[Path, Path],
    next_num: Callable,
    secho: EchoWrapper,
    pm: pluggy.PluginManager,
    config_data: PoodleConfigData,
) -> list[CleanRunTrial]:
    """Run a trial on each source folder with no mutation."""
    return [
        clean_run_trial(
            source_folder,
            folder_zips[source_folder],
            next_num,
            secho,
            pm,
            config_data,
        )
        for source_folder in config_data.source_folders
    ]


def clean_run_trial(
    source_folder: Path,
    folder_zip: Path,
    next_num: Callable,
    secho: EchoWrapper,
    pm: pluggy.PluginManager,
    config_data: PoodleConfigData,
) -> MutantTrial:
    """Run a trial with no mutation."""
    start = time.time()
    secho(f"Testing clean run of folder '{source_folder}'...", nl=False)

    run_id = next_num()
    run_folder = setup_run_folder(run_id, folder_zip, None, config_data)

    logger.debug("START: run_id=%s run_folder=%s", run_id, run_folder)

    test_run_result: RunResult = pm.hook.run_testing(
        run_folder=run_folder,
        timeout=None,
        config=config_data,
        secho=secho,
        source_folder=source_folder,
        mutant=None,
    )

    delete_folder(run_folder, config_data)

    duration = time.time() - start
    logger.debug("END: run_id=%s - Elapsed Time %.2f s", run_id, duration)

    if test_run_result.result != RunResult.RESULT_PASSED:
        secho(style("FAILED", fg="red"))
        raise PoodleTrialRunError("Clean Run Failed", test_run_result.description)

    secho("PASSED")
    logger.info("Elapsed Time %.2f s", time.time() - start)

    return CleanRunTrial(
        source_folder=source_folder,
        result=test_run_result,
        duration=duration,
    )


def run_mutant_trails(
    mutants: list[Mutant],
    folder_zips: dict[Path, Path],
    next_num: Callable,
    timeout: float,
    secho: EchoWrapper,
    pm: pluggy.PluginManager,
    config_data: PoodleConfigData,
) -> TestingResults:
    """Run the Mutant Trials and collect results.

    Report status as execution proceeds.
    """
    start = time.time()
    secho("Testing mutants")
    with concurrent.futures.ProcessPoolExecutor(max_workers=config_data.max_workers) as executor:
        try:
            pm_dump = dill.dumps(pm)
            config_data_dump = dill.dumps(config_data)
            futures = [
                executor.submit(
                    run_mutant_trial,
                    next_num(),
                    folder_zips[mutant.source_folder],
                    mutant,
                    timeout,
                    secho,
                    pm_dump,
                    config_data_dump,
                )
                for mutant in mutants
            ]
            print("submitted")

            summary = TestingSummary()
            summary.trials = len(mutants)
            pad = int(math.log(summary.trials, 10) + 1)

            for future in concurrent.futures.as_completed(futures):
                if future.cancelled():
                    secho("Canceled")
                else:
                    mutant_trial: MutantTrial = future.result()
                    summary += mutant_trial.result
                    secho(
                        f"COMPLETED {summary.tested:>{pad}}/{summary.trials:<{pad}}   "
                        f"FOUND {summary.found:>{pad}}   "
                        f"NOT FOUND {summary.not_found:>{pad}}   "
                        f"TIMEOUT {summary.timeout:>{pad}}   "
                        f"ERRORS {summary.errors:>{pad}}",
                    )
        except KeyboardInterrupt:
            secho("Received Keyboard Interrupt.  Cancelling Remaining Trials.")
            executor.shutdown(wait=True, cancel_futures=True)
            raise

    logger.info("Elapsed Time %.2f s", time.time() - start)

    return TestingResults(
        mutant_trials=[future.result() for future in futures],
        summary=summary,
    )


def run_mutant_trial(  # noqa: PLR0913
    run_id: str,
    folder_zip: Path,
    mutant: Mutant,
    timeout: float | None,
    secho: EchoWrapper,
    pm_dump: bytes,
    config_data_dump: bytes,
) -> MutantTrial:
    pm: pluggy.PluginManager = dill.loads(pm_dump)
    config_data: PoodleConfigData = dill.loads(config_data_dump)

    start = time.time()
    logging.basicConfig(format=config_data.log_format, level=config_data.log_level)

    logger.debug(
        "SETUP: run_id=%s folder_zip=%s file=%s:%s text='%s'",
        run_id,
        folder_zip,
        mutant.source_file,
        mutant.lineno,
        mutant.text,
    )

    run_folder = setup_run_folder(run_id, folder_zip, mutant, config_data)

    logger.debug("START: run_id=%s run_folder=%s", run_id, run_folder)

    test_run_result: RunResult = pm.hook.run_testing(
        run_folder=run_folder,
        timeout=timeout,
        config=config_data,
        secho=secho,
        source_folder=mutant.source_folder,
        mutant=mutant,
    )

    if test_run_result.result == RunResult.RESULT_PASSED:
        result = MutantTrialResult(
            found=False,
            reason_code=MutantTrialResult.RC_NOT_FOUND,
        )
    elif test_run_result.result == RunResult.RESULT_FAILED:
        result = MutantTrialResult(
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        )
    elif test_run_result.result == RunResult.RESULT_TIMEOUT:
        result = MutantTrialResult(
            found=False,
            reason_code=MutantTrialResult.RC_TIMEOUT,
            reason_desc=test_run_result.description,
        )
    else:
        result = MutantTrialResult(
            found=True,
            reason_code=MutantTrialResult.RC_OTHER,
            reason_desc=test_run_result.description,
        )

    delete_folder(run_folder, config_data)

    duration = time.time() - start
    logger.debug("END: run_id=%s - Elapsed Time %.2f s", run_id, duration)

    return MutantTrial(mutant=mutant, result=result, duration=duration)


def setup_run_folder(
    run_id: str,
    folder_zip: Path,
    mutant: Mutant | None,
    config_data: PoodleConfigData,
):
    logger.debug("setup_run_folder: run_id=%s", run_id)

    run_folder = config_data.work_folder / ("run-" + run_id)
    run_folder.mkdir()

    with ZipFile(folder_zip, "r") as zip_file:
        zip_file.extractall(run_folder)

    if mutant and mutant.source_file:
        target_file = run_folder / mutant.source_file
        file_lines = target_file.read_text("utf-8").splitlines(keepends=True)
        file_lines = mutate_lines(mutant, file_lines)
        target_file.write_text(data="".join(file_lines), encoding="utf-8")

    return run_folder
