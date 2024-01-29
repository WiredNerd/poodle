"""Poodle core run process."""

from __future__ import annotations

import logging

from . import __version__
from .common.config import PoodleConfigData
from .common.echo_wrapper import EchoWrapper
from .common.exceptions import PoodleNoMutantsFoundError
from .common.file_utils import create_temp_zips, delete_folder
from .common.id_gen import IdentifierGenerator
from .common.util import calc_timeout, create_unified_diff, pprint_str
from .mutate import create_mutants_for_all_mutators
from .plugins import plugin_manager as pm
from .run import clean_run_each_source_folder, run_mutant_trails

logger = logging.getLogger(__name__)


def main_process(config_data: PoodleConfigData, secho: EchoWrapper) -> None:
    """Poodle core run process."""
    id_gen = IdentifierGenerator()
    print_header(config_data, secho)
    logger.info("\n%s", pprint_str(vars(config_data)))

    delete_folder(config_data.work_folder, config_data)
    folder_zips = create_temp_zips(config_data, id_gen)

    mutants = create_mutants_for_all_mutators(secho, config_data, pm)
    if not mutants:
        raise PoodleNoMutantsFoundError("No mutants were found to test!")
    secho(f"Identified {len(mutants)} mutants")
    pm.hook.filter_mutations(mutants=mutants, config=config_data, secho=secho)

    clean_run_results = clean_run_each_source_folder(folder_zips, id_gen, secho, pm, config_data)
    timeout = calc_timeout(config_data, clean_run_results)
    results = run_mutant_trails(mutants, folder_zips, id_gen, timeout, secho, pm, config_data)

    for trial in results.mutant_trials:
        trial.mutant.unified_diff = create_unified_diff(trial.mutant)

    pm.hook.report_results(testing_results=results, config=config_data, secho=secho)

    delete_folder(config_data.work_folder, config_data)

    # if config.fail_under and results.summary.success_rate < config.fail_under / 100:
    #     display_fail_under = display_percent(config.fail_under / 100)
    #     msg = f"Mutation score {results.summary.coverage_display} is below goal of {display_fail_under}"
    #     raise PoodleTestingFailedError(msg)


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


def print_header(config_data: PoodleConfigData, secho: EchoWrapper) -> None:
    """Print a header to the console."""
    secho(poodle_header_str.format(version=__version__), fg="cyan")
    secho("Running with the following configuration:")
    secho(f" - Source Folders: {[str(folder) for folder in config_data.source_folders]}")
    secho(f" - Config File:    {config_data.config_file}")
    secho(f" - Max Workers:    {config_data.max_workers}")
    secho(f" - Runner:         {config_data.runner}")
    secho(f" - Reporters:      {list(config_data.reporters)}")
    # if config_data.fail_under:
    #     secho(f" - Coverage Goal:  {config_data.fail_under:.2f}%")
    secho()
