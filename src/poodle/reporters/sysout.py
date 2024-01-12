"""Mutation Test Result SYSOUT Reporter."""

from __future__ import annotations

from typing import Callable

import pluggy

from poodle import PoodleConfigData, PoodleOptionCollector, TestingResults, TestingSummary

hookimpl = pluggy.HookimplMarker("poodle")


class SysoutReporter:
    show_not_found = True

    @hookimpl(specname="add_options")
    def add_options(self, options: PoodleOptionCollector) -> None:
        options.add_file_option("display_not_found", "Show not found Mutations in sysout.")

    @hookimpl(specname="configure")
    def configure(self, config: PoodleConfigData) -> None:
        self.show_not_found = config.get_bool_from_config("display_not_found")
        self.show_not_found = True if self.show_not_found is None else self.show_not_found

    @hookimpl(specname="report_results")
    def report_sysout(self, testing_results: TestingResults, secho: Callable) -> None:
        """Echo quick summary to console."""
        self.report_summary(testing_results.summary, secho)
        if self.show_not_found:
            self.report_not_found(testing_results, secho)

    def report_summary(self, summary: TestingSummary, secho: Callable) -> None:
        """Echo quick summary to console."""
        if summary.trials < 1:
            secho("!!! No mutants found to test !!!", fg="yellow")
            return

        secho("")
        secho("*** Results Summary ***", fg="green")
        secho(f"Testing found {summary.success_rate:.1%} of Mutants.")
        if summary.not_found:
            secho(f" - {summary.not_found} mutant(s) were not found.")
        if summary.timeout:
            secho(f" - {summary.timeout} mutant(s) caused trial to timeout.")
        if summary.errors:
            secho(f" - {summary.errors} mutant(s) could not be tested due to an error.")

    def report_not_found(self, testing_results: TestingResults, secho: Callable) -> None:
        """Echo information about Trials that did not pass."""
        failed_trials = [trial for trial in testing_results.mutant_trials if not trial.result.found]
        if not failed_trials:
            return

        failed_trials.sort(
            key=lambda trial: (
                trial.mutant.source_folder,
                str(trial.mutant.source_file) or "",
                trial.mutant.lineno,
                trial.mutant.mutator_name,
            )
        )

        secho("")
        secho("*** Mutants Not Found ***", fg="yellow")
        for trial in failed_trials:
            mutant = trial.mutant
            result = trial.result

            secho("")
            secho(f"Mutant Trial Result: {result.reason_code}")
            secho(f"Mutator: {mutant.mutator_name}")
            if result.reason_desc:
                secho(result.reason_desc)

            if mutant.unified_diff:
                secho(mutant.unified_diff)
            else:
                secho(
                    f"source_file={mutant.source_file} lineno={mutant.lineno} col_offset={mutant.col_offset} "
                    f"end_lineno={mutant.end_lineno} end_col_offset={mutant.end_col_offset}"
                )
                secho("text:")
                secho(mutant.text)
