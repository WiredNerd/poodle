"""Run Mutation Trials."""

from __future__ import annotations

import concurrent.futures
import logging
import shutil
import time
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

from click import style

from . import PoodleTrialRunError
from .data_types import Mutant, MutantTrial, MutantTrialResult, PoodleConfig, PoodleWork, TestingResults, TestingSummary
from .runners import command_line
from .util import dynamic_import, update_summary

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


def clean_run_each_source_folder(work: PoodleWork) -> None:
    """Run a trial on each source folder with no mutation."""
    for folder in work.config.source_folders:
        clean_run_trial(work, folder)


def clean_run_trial(work: PoodleWork, folder: Path) -> None:
    """Run a trial with no mutation."""
    start = time.time()
    work.echo(f"Testing clean run of folder '{folder}'...", nl=False)
    mutant_trial = run_mutant_trial(
        work.config,
        work.echo,
        work.folder_zips[folder],
        Mutant(
            source_folder=folder,
            source_file=None,
            lineno=0,
            col_offset=0,
            end_lineno=0,
            end_col_offset=0,
            text="",
        ),
        work.next_num(),
        work.runner,
    )
    if mutant_trial.result.passed:  # not expected
        work.echo(style("FAILED", fg="red"))
        raise PoodleTrialRunError("Clean Run Failed", mutant_trial.result.reason_desc)

    work.echo("PASSED")
    logger.info("Elapsed Time %.2f s", time.time() - start)


def run_mutant_trails(work: PoodleWork, mutants: list[Mutant]) -> TestingResults:
    """Run the Mutant Trials and collect results.

    Report status as execution proceeds.
    """
    start = time.time()
    work.echo("Testing mutants")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_mutant_trial,
                work.config,
                work.echo,
                work.folder_zips[mutant.source_folder],
                mutant,
                work.next_num(),
                work.runner,
            )
            for mutant in mutants
        ]

        summary = TestingSummary()
        num_trials = len(mutants)
        for future in concurrent.futures.as_completed(futures):
            if future.cancelled():
                work.echo("Canceled")
            else:
                mutant_trial: MutantTrial = future.result()
                update_summary(summary, mutant_trial.result)
            work.echo(
                f"COMPLETED {summary.tested:>4}/{num_trials:<4}"
                f"\tFOUND {summary.found:>4}"
                f"\tNOT FOUND {summary.not_found:>4}"
                f"\tTIMEOUT {summary.timeout:>4}"
                f"\tERRORS {summary.errors:>4}",
            )

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
        target_file = Path(run_folder / mutant.source_file)
        file_lines = target_file.read_text("utf-8").splitlines(keepends=True)

        prefix = file_lines[mutant.lineno - 1][: mutant.col_offset]
        suffix = file_lines[mutant.end_lineno - 1][mutant.end_col_offset :]

        file_lines[mutant.lineno - 1] = prefix + mutant.text + suffix
        for _ in range(mutant.lineno, mutant.end_lineno):
            file_lines.pop(mutant.lineno)

        target_file.write_text(data="".join(file_lines), encoding="utf-8")

    logger.debug("START: run_id=%s", run_id)

    result: MutantTrialResult = runner(
        config=config,
        echo=echo,
        run_folder=run_folder,
        mutant=mutant,
    )

    shutil.rmtree(run_folder)

    logger.debug("END: run_id=%s - Elapsed Time %.2f s", run_id, time.time() - start)

    return MutantTrial(mutant, result)
