"""Poodle core run process."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

from . import PoodleNoMutantsFoundError, PoodleTestingFailedError, __version__
from .data_types import PoodleConfig, PoodleWork
from .mutate import create_mutants_for_all_mutators, initialize_mutators
from .report import generate_reporters
from .run import clean_run_each_source_folder, get_runner, run_mutant_trails
from .util import calc_timeout, create_temp_zips, create_unified_diff, display_percent, pprint_str

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def main_process(config: PoodleConfig) -> None:
    """Poodle core run process."""
    work = PoodleWork(config)  # sets logging defaults
    print_header(work)
    logger.info("\n%s", pprint_str(config))

    delete_folder(config.work_folder)
    create_temp_zips(work)

    work.mutators = initialize_mutators(work)
    work.runner = get_runner(config)
    work.reporters = list(generate_reporters(config))

    mutants = create_mutants_for_all_mutators(work)
    if not mutants:
        raise PoodleNoMutantsFoundError("No mutants were found to test!")
    work.echo(f"Identified {len(mutants)} mutants")

    clean_run_results = clean_run_each_source_folder(work)
    timeout = calc_timeout(config, clean_run_results)
    results = run_mutant_trails(work, mutants, timeout)

    for trial in results.mutant_trials:
        trial.mutant.unified_diff = create_unified_diff(trial.mutant)

    for reporter in work.reporters:
        reporter(config=config, echo=work.echo, testing_results=results)

    delete_folder(config.work_folder)

    if config.fail_under and results.summary.success_rate < config.fail_under / 100:
        display_fail_under = display_percent(config.fail_under / 100)
        msg = f"Mutation score {results.summary.coverage_display} is below goal of {display_fail_under}"
        raise PoodleTestingFailedError(msg)


poodle_header_str = r"""
|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|\/|
    ____                  ____         ''',
   / __ \____  ____  ____/ / /__    o_)O \)____)"
  / /_/ / __ \/ __ \/ __  / / _ \    \_        )
 / ____/ /_/ / /_/ / /_/ / /  __/      '',,,,,,
/_/    \____/\____/\__,_/_/\___/         ||  ||
Mutation Tester Version {version:<15} "--'"--'
|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|/\|

"""


def print_header(work: PoodleWork) -> None:
    """Print a header to the console."""
    work.echo(poodle_header_str.format(version=__version__), fg="cyan")
    work.echo("Running with the following configuration:")
    work.echo(f" - Source Folders: {[str(folder) for folder in work.config.source_folders]}")
    work.echo(f" - Config File:    {work.config.config_file}")
    work.echo(f" - Max Workers:    {work.config.max_workers}")
    work.echo(f" - Runner:         {work.config.runner}")
    work.echo(f" - Reporters:      {work.config.reporters}")
    if work.config.fail_under:
        work.echo(f" - Coverage Goal:  {work.config.fail_under:.2f}%")
    work.echo()


def delete_folder(folder: Path) -> None:
    """Delete a folder."""
    if folder.exists():
        logger.info("delete %s", folder)
        shutil.rmtree(folder)
