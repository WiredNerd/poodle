"""Mutation Test Result JSON Reporter."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import click
import pluggy

from poodle import PoodleConfigData, PoodleOptionCollector, TestingResults
from poodle.common.util import to_json

hookimpl = pluggy.HookimplMarker("poodle")


class JsonReporter:
    enabled = False
    include_found = False
    include_not_found = True
    include_summary = True
    report_file = "mutation-testing-report.json"

    @hookimpl(specname="add_options")
    def add_options(self, options: PoodleOptionCollector) -> None:
        options.add_cli_option("--json", help="File to create with JSON report.")
        options.add_file_option("json_reporter.report_file", "File to create with JSON report.")
        options.add_file_option("json_reporter.include_found", "Include found mutants in JSON report.")
        options.add_file_option("json_reporter.include_not_found", "Include not found mutants in JSON report.")
        options.add_file_option("json_reporter.include_summary", "Include summary in JSON report.")

    @hookimpl(specname="configure")
    def configure(self, config: PoodleConfigData) -> None:
        if config.cmd_kwargs.get("json", ""):
            config.reporters.add("json")
        if "json" in config.reporters:
            self.enabled = True

        json = config.merge_dict_from_config("json_reporter")

        self.report_file = json.get("report_file", self.report_file)
        self.include_found = json.get("include_found", False)
        self.include_not_found = json.get("include_not_found", True)
        self.include_summary = json.get("include_summary", True)

    @hookimpl(specname="report_results")
    def report_json(self, testing_results: TestingResults, secho: Callable) -> None:
        """Create JSON file with test results."""
        if not self.enabled:
            return

        include_statuses = self.get_include_statuses()
        mutant_trials = [trial for trial in testing_results.mutant_trials if trial.result.found in include_statuses]

        out_results = TestingResults(
            summary=testing_results.summary if self.include_summary else [],
            mutant_trials=mutant_trials,
        )

        if self.report_file == "sysout":
            secho(to_json(out_results, indent=4), fg="yellow")
        else:
            Path(self.report_file).write_text(to_json(out_results))

        secho("")
        secho(f"JSON report written to {self.report_file!s}", fg="green")

    def get_include_statuses(self) -> set[bool]:
        """Get set of statuses to include in report."""
        include_statuses = set()
        if self.include_found:
            include_statuses.add(True)  # noqa: FBT003
        if self.include_not_found:
            include_statuses.add(False)  # noqa: FBT003
        return include_statuses
