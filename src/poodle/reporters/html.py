"""Mutation Test Result HTML Reporter."""

from __future__ import annotations

import datetime
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from jinja2 import Environment, PackageLoader

from poodle import __version__ as poodle_version
from poodle.data_types import MutantTrial, PoodleConfig, TestingResults, TestingSummary

if TYPE_CHECKING:
    from collections.abc import Generator


def template_path() -> Path:
    """Return the path to the HTML Template folder."""
    return Path(__file__).parent.parent / "templates"


STATIC_FILES = [
    "html-report.js",
    "html-report.css",
    "poodle.ico",
]


def report_html(config: PoodleConfig, echo: Callable, testing_results: TestingResults, *_, **__) -> None:
    """Build HTML Report for Testing Results."""
    html_options = config.reporter_opts.get("html", {})
    if not isinstance(html_options, dict):
        raise TypeError("HTML Reporter Options (reporter_opts.html) must be a Dictionary.")

    report_folder = Path(html_options.get("report_folder", "mutation_reports"))
    copy_static_files(report_folder)

    env = Environment(loader=PackageLoader("poodle"), autoescape=True)

    common_vars = {
        "project": {
            "name": config.project_name,
            "version": config.project_version,
        },
        "poodle_version": poodle_version,
        "timestamp": local_timestamp(),
    }

    modules = module_data(testing_results, html_options)

    index_template = env.get_template("html-report-index.html.jinja")
    index_page = index_template.render(total=testing_results.summary, modules=modules, **common_vars)
    index_file = report_folder / "index.html"
    index_file.write_text(index_page.strip(), encoding="utf-8")

    module_template = env.get_template("html-report-module.html.jinja")
    for source_file, module in modules.items():
        module_page = module_template.render(source_file=source_file, module=module, **common_vars)
        (report_folder / module["report_file"]).write_text(module_page.strip(), encoding="utf-8")

    echo(f"HTML Report Generated at {index_file.resolve()}")


def copy_static_files(report_folder: Path) -> None:
    """Copy static files to report folder."""
    report_folder.mkdir(parents=True, exist_ok=True)
    templates_folder = template_path()
    for file in STATIC_FILES:
        shutil.copy2(templates_folder / file, report_folder / file)


def local_timestamp() -> str:
    """Return a local timestamp."""
    dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S%z")


def module_data(testing_results: TestingResults, html_options: dict) -> dict[Path, dict[str, Any]]:
    """Return data for report pages."""
    modules = {trial.mutant.source_file for trial in testing_results.mutant_trials if trial.mutant.source_file}

    module_dict: dict[Path, dict] = {m: dict() for m in modules}  # noqa: C408 - `dict()` call is needed here
    include_found_index = html_options.get("include_found_trials_on_index", False)
    include_found_source = html_options.get("include_found_trials_with_source", True)

    for idx, module in enumerate(modules, start=1):
        module_dict[module]["report_file"] = f"module-{idx}.html"
        module_dict[module]["file_id"] = re.sub(r"[^A-Za-z0-9\-_:.]", "_", str(module))

        module_dict[module]["trials"] = list(module_trials(module, testing_results.mutant_trials))
        module_dict[module]["trials"].sort(key=lambda trial: trial.mutant.lineno)

        module_dict[module]["lines"] = list(module_lines(module))
        module_add_trials_to_lines(module_dict[module]["trials"], module_dict[module]["lines"], include_found_source)

        module_dict[module]["summary"] = module_summary(module_dict[module]["trials"])

        if not include_found_index:
            module_dict[module]["trials"] = remove_found_trials(module_dict[module]["trials"])

    return module_dict


def module_trials(
    module: Path,
    mutant_trials: list[MutantTrial],
) -> Generator[MutantTrial, Any, None]:
    """Return trials for a module."""
    for trial in mutant_trials:
        if trial.mutant.source_file == module:
            yield trial


def module_lines(module: Path) -> Generator[dict[str, Any], Any, None]:
    """Return lines for a module."""
    for lineno, line in enumerate(module.read_text("utf-8").splitlines(), start=1):
        yield {
            "lineno": lineno,
            "text": line,
            "trials": [],
            "row_class": "plain",
        }


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


def module_summary(module_trials: list[MutantTrial]) -> TestingSummary:
    """Return summary for a module."""
    summary = TestingSummary()
    for trial in module_trials:
        summary += trial.result
    summary.trials = len(module_trials)
    return summary


def remove_found_trials(trials: list[MutantTrial]) -> list[MutantTrial]:
    """Remove not found trials from a list of trials."""
    return [trial for trial in trials if not trial.result.found]
