"""Mutation Test Result HTML Reporter."""

from __future__ import annotations

import datetime
import re
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
import pluggy
from jinja2 import Environment, PackageLoader

from poodle import EchoWrapper, MutantTrial, PoodleConfigData, PoodleOptionCollector, TestingResults, TestingSummary
from poodle import __version__ as poodle_version

if TYPE_CHECKING:
    from collections.abc import Generator

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register HTML Reporter Class."""
    plugin_manager.register(HtmlReporter())


class HtmlReporter:
    def template_path(self) -> Path:
        """Return the path to the HTML Template folder."""
        return Path(__file__).parent.parent / "templates"

    STATIC_FILES = [
        "html-report.js",
        "html-report.css",
        "poodle.ico",
    ]

    enabled = False
    report_folder = Path("mutation_reports")
    include_found_trials_on_index = False
    include_found_trials_with_source = True

    @hookimpl(specname="add_options")
    def add_options(self, options: PoodleOptionCollector) -> None:
        options.add_cli_option("--html", help="Folder to create with HTML report.", type=click.Path(path_type=Path))
        options.add_group_description("html_reporter", "HTML Reporter Options in dict.")
        options.add_file_option(
            group="html_reporter",
            field_name=".report_folder",
            description="Folder name to store HTML report in.",
        )
        options.add_file_option(
            group="html_reporter",
            field_name=".include_found_trials_on_index",
            description="Include found trials on index page.",
        )
        options.add_file_option(
            group="html_reporter",
            field_name=".include_found_trials_with_source",
            description="Include found trials with source code pages.",
        )

    @hookimpl(specname="configure")
    def configure(self, config: PoodleConfigData) -> None:
        if "html" in config.cmd_kwargs:
            config.reporters.add("html")
        if "html" in config.reporters:
            self.enabled = True

        html = config.merge_dict_from_config("html_reporter")

        self.report_folder = Path(html.get("report_folder", self.report_folder))
        if config.cmd_kwargs["html"]:
            self.report_folder = Path(config.cmd_kwargs["html"])
        self.include_found_trials_on_index = html.get(
            "include_found_trials_on_index", self.include_found_trials_on_index
        )
        self.include_found_trials_with_source = html.get(
            "include_found_trials_with_source", self.include_found_trials_with_source
        )

    @hookimpl(specname="report_results")
    def report_html(self, secho: EchoWrapper, testing_results: TestingResults, config: PoodleConfigData) -> None:
        """Build HTML Report for Testing Results."""
        if not self.enabled:
            return

        self.copy_static_files()

        env = Environment(loader=PackageLoader("poodle"), autoescape=True)

        common_vars = {
            "project": {
                "name": config.project_name,
                "version": config.project_version,
            },
            "poodle_version": poodle_version,
            "timestamp": self.local_timestamp(),
        }

        modules = self.module_data(testing_results)

        index_template = env.get_template("html-report-index.html.jinja")
        index_page = index_template.render(total=testing_results.summary, modules=modules, **common_vars)
        index_file = self.report_folder / "index.html"
        index_file.write_text(index_page.strip(), encoding="utf-8")

        module_template = env.get_template("html-report-module.html.jinja")
        for source_file, module in modules.items():
            module_page = module_template.render(source_file=source_file, module=module, **common_vars)
            (self.report_folder / module["report_file"]).write_text(module_page.strip(), encoding="utf-8")

        secho("")
        secho(f"HTML Report Generated at {index_file.resolve()}", fg="green")

    def copy_static_files(self) -> None:
        """Copy static files to report folder."""
        self.report_folder.mkdir(parents=True, exist_ok=True)
        templates_folder = self.template_path()
        for file in self.STATIC_FILES:
            shutil.copy2(templates_folder / file, self.report_folder / file)

    @staticmethod
    def local_timestamp() -> str:
        """Return a local timestamp."""
        dt = datetime.datetime.now(datetime.timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S%z")

    def module_data(self, testing_results: TestingResults) -> dict[Path, dict[str, Any]]:
        """Return data for report pages."""
        modules = {trial.mutant.source_file for trial in testing_results.mutant_trials if trial.mutant.source_file}

        module_dict: dict[Path, dict] = {m: dict() for m in modules}  # noqa: C408 - `dict()` call is needed here

        for idx, module in enumerate(modules, start=1):
            module_dict[module]["report_file"] = f"module-{idx}.html"
            module_dict[module]["file_id"] = re.sub(r"[^A-Za-z0-9\-_:.]", "_", str(module))

            module_dict[module]["trials"] = list(self.module_trials(module, testing_results.mutant_trials))
            module_dict[module]["trials"].sort(key=lambda trial: trial.mutant.lineno)

            module_dict[module]["lines"] = list(self.module_lines(module))
            self.module_add_trials_to_lines(
                module_dict[module]["trials"], module_dict[module]["lines"], self.include_found_trials_with_source
            )

            module_dict[module]["summary"] = self.module_summary(module_dict[module]["trials"])

            if not self.include_found_trials_on_index:
                module_dict[module]["trials"] = self.remove_found_trials(module_dict[module]["trials"])

        return OrderedDict(sorted(module_dict.items(), key=lambda item: item[0]))

    @staticmethod
    def module_trials(module: Path, mutant_trials: list[MutantTrial]) -> Generator[MutantTrial, Any, None]:
        """Return trials for a module."""
        for trial in mutant_trials:
            if trial.mutant.source_file == module:
                yield trial

    @staticmethod
    def module_lines(module: Path) -> Generator[dict[str, Any], Any, None]:
        """Return lines for a module."""
        for lineno, line in enumerate(module.read_text("utf-8").splitlines(), start=1):
            yield {
                "lineno": lineno,
                "text": line,
                "trials": [],
                "row_class": "plain",
            }

    @staticmethod
    def module_add_trials_to_lines(
        module_trials: list[MutantTrial],
        module_lines: list[dict[str, Any]],
        include_found: bool,
    ) -> None:
        """Add trials to lines."""
        for trial in module_trials:
            if include_found or not trial.result.found:
                line = module_lines[trial.mutant.lineno - 1]
                line["trials"].append(trial)
                if line["row_class"] == "plain":
                    line["row_class"] = "found" if trial.result.found else "not_found"
                elif (line["row_class"] == "found" and not trial.result.found) or (
                    line["row_class"] == "not_found" and trial.result.found
                ):
                    line["row_class"] = "partial_found"

    @staticmethod
    def module_summary(module_trials: list[MutantTrial]) -> TestingSummary:
        """Return summary for a module."""
        summary = TestingSummary()
        for trial in module_trials:
            summary += trial.result
        summary.trials = len(module_trials)
        return summary

    @staticmethod
    def remove_found_trials(trials: list[MutantTrial]) -> list[MutantTrial]:
        """Remove not found trials from a list of trials."""
        return [trial for trial in trials if not trial.result.found]
