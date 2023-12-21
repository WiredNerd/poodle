"""Run Mutation Trials."""

from __future__ import annotations

import concurrent.futures
import logging
import shutil
import time
from typing import TYPE_CHECKING, Callable
from zipfile import ZipFile

from click import style

from . import PoodleTrialRunError
from .data_types import Mutant, MutantTrial, MutantTrialResult, PoodleConfig, PoodleWork, TestingResults, TestingSummary
from .runners import command_line
from .util import dynamic_import, mutate_lines

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

builtin_runners = {
    "command_line": command_line.runner,
}


def get_runner(config: PoodleConfig) -> Callable:
    """Retrieve runner callable given internal runner name or external runner python name."""
    logger.debug("Runner: %s", config.runner)

    if config.runner in builtin_runners:
        return builtin_runners[config.runner]

    return dynamic_import(config.runner)


def clean_run_each_source_folder(work: PoodleWork) -> dict[Path, MutantTrial]:
    """Run a trial on each source folder with no mutation."""
    return {folder: clean_run_trial(work, folder) for folder in work.config.source_folders}


def clean_run_trial(work: PoodleWork, folder: Path) -> MutantTrial:
    """Run a trial with no mutation."""
    start = time.time()
    work.echo(f"Testing clean run of folder '{folder}'...", nl=False)
    mutant_trial = run_mutant_trial(
        config=work.config,
        echo=work.echo,
        folder_zip=work.folder_zips[folder],
        mutant=Mutant(
            mutator_name="",
            source_folder=folder,
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        ),
        run_id=work.next_num(),
        runner=work.runner,
        timeout=None,
    )
    if mutant_trial.result.found:  # not expected
        work.echo(style("FAILED", fg="red"))
        raise PoodleTrialRunError("Clean Run Failed", mutant_trial.result.reason_desc)

    work.echo("PASSED")
    logger.info("Elapsed Time %.2f s", time.time() - start)

    return mutant_trial


def run_mutant_trails(work: PoodleWork, mutants: list[Mutant], timeout: float) -> TestingResults:
    """Run the Mutant Trials and collect results.

    Report status as execution proceeds.
    """
    start = time.time()
    work.echo("Testing mutants")
    with concurrent.futures.ProcessPoolExecutor(max_workers=work.config.max_workers) as executor:
        try:
            futures = [
                executor.submit(
                    run_mutant_trial,
                    work.config,
                    work.echo,
                    work.folder_zips[mutant.source_folder],
                    mutant,
                    work.next_num(),
                    work.runner,
                    timeout,
                )
                for mutant in mutants
            ]

            summary = TestingSummary()
            summary.trials = len(mutants)
            for future in concurrent.futures.as_completed(futures):
                if future.cancelled():
                    work.echo("Canceled")
                else:
                    mutant_trial: MutantTrial = future.result()
                    summary += mutant_trial.result
                    work.echo(
                        f"COMPLETED {summary.tested:>4}/{summary.trials:<4}"
                        f"\tFOUND {summary.found:>4}"
                        f"\tNOT FOUND {summary.not_found:>4}"
                        f"\tTIMEOUT {summary.timeout:>4}"
                        f"\tERRORS {summary.errors:>4}",
                    )
        except KeyboardInterrupt:
            work.echo("Received Keyboard Interrupt.  Cancelling Remaining Trials.")
            executor.shutdown(wait=True, cancel_futures=True)
            raise

    logger.info("Elapsed Time %.2f s", time.time() - start)

    return TestingResults(
        mutant_trials=[future.result() for future in futures],
        summary=summary,
    )


def run_mutant_trial(  # noqa: PLR0913
    config: PoodleConfig,
    echo: Callable,
    folder_zip: Path,
    mutant: Mutant,
    run_id: str,
    runner: Callable,
    timeout: float | None,
) -> MutantTrial:
    """Run Trial for specified Mutant.

    Create a Run Folder.
    Unzip the zip file to the Run Folder.
    Apply Mutation.
    Call the Trial Runner.
    Delete the Run Folder.
    Return MutantTrial with result data.
    """
    start = time.time()
    logging.basicConfig(format=config.log_format, level=config.log_level)

    logger.debug(
        "SETUP: run_id=%s folder_zip=%s file=%s:%s text='%s'",
        run_id,
        folder_zip,
        mutant.source_file,
        mutant.lineno,
        mutant.text,
    )

    run_folder = config.work_folder / ("run-" + run_id)
    run_folder.mkdir()

    with ZipFile(folder_zip, "r") as zip_file:
        zip_file.extractall(run_folder)

    if mutant.source_file:
        target_file = run_folder / mutant.source_file
        file_lines = target_file.read_text("utf-8").splitlines(keepends=True)
        file_lines = mutate_lines(mutant, file_lines)
        target_file.write_text(data="".join(file_lines), encoding="utf-8")

    logger.debug("START: run_id=%s run_folder=%s", run_id, run_folder)

    result: MutantTrialResult = runner(
        config=config,
        echo=echo,
        run_folder=run_folder,
        mutant=mutant,
        timeout=timeout,
    )

    shutil.rmtree(run_folder)

    duration = time.time() - start
    logger.debug("END: run_id=%s - Elapsed Time %.2f s", run_id, duration)

    return MutantTrial(mutant=mutant, result=result, duration=duration)
