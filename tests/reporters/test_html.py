from __future__ import annotations

import datetime
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree

import pytest

import poodle
from poodle.data_types import Mutant, MutantTrial, MutantTrialResult, TestingResults, TestingSummary
from poodle.reporters import html
from tests.data_types.test_data import PoodleConfigStub


def create_mutant_trial(
    source_file: Path,
    mutator_name: str,
    lineno: int,
    text: str,
    unified_diff: str,
    found: bool,
    reason_code: str,
    reason_desc: str | None = None,
) -> MutantTrial:
    return MutantTrial(
        mutant=Mutant(
            source_file=source_file,
            mutator_name=mutator_name,
            lineno=lineno,
            col_offset=4,
            end_lineno=lineno,
            end_col_offset=10,
            text=text,
            source_folder=source_file.parent,
            unified_diff=unified_diff,
        ),
        result=MutantTrialResult(
            found=found,
            reason_code=reason_code,
            reason_desc=reason_desc,
        ),
        duration=1.0,
    )


module_augassign = """from __future__ import annotations


def addition_assign(x, y):
    x += y
    return x


def subtraction_assign(x, y):
    x -= y
    return x


def multiplication_assign(x, y):
    x *= y
    return x
"""


@pytest.fixture()
def mutant_trials_augassign() -> list[MutantTrial]:
    return build_mutant_trials_augassign()


def build_mutant_trials_augassign() -> list[MutantTrial]:
    return [
        create_mutant_trial(
            source_file=Path("example/src/augassign.py"),
            mutator_name="BinOp",
            lineno=5,
            text="x -= y",
            unified_diff="@@ -5,1 +5,1 @@\n-    x += y\n+    x -= y\n",
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        ),
        create_mutant_trial(
            source_file=Path("example/src/augassign.py"),
            mutator_name="BinOp",
            lineno=10,
            text="x += y",
            unified_diff="@@ -5,1 +5,1 @@\n-    x -= y\n+    x += y\n",
            found=False,
            reason_code=MutantTrialResult.RC_NOT_FOUND,
        ),
        create_mutant_trial(
            source_file=Path("example/src/augassign.py"),
            mutator_name="BinOp",
            lineno=15,
            text="x += y",
            unified_diff="@@ -5,1 +5,1 @@\n-    x *= y\n+    x += y\n",
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        ),
        create_mutant_trial(
            source_file=Path("example/src/augassign.py"),
            mutator_name="BinOp",
            lineno=15,
            text="x /= y",
            unified_diff="@@ -5,1 +5,1 @@\n-    x *= y\n+    x /= y\n",
            found=False,
            reason_code=MutantTrialResult.RC_OTHER,
            reason_desc="Mutant raised exception: ZeroDivisionError('division by zero')",
        ),
    ]


module_compare = """from __future__ import annotations


def equals(a, b):
    return a == b


def less_than(a, b):
    return a < b


def less_than_equal(a, b):
    return a <= b
"""


@pytest.fixture()
def mutant_trials_compare() -> list[MutantTrial]:
    return build_mutant_trials_compare()


def build_mutant_trials_compare() -> list[MutantTrial]:
    return [
        create_mutant_trial(
            source_file=Path("example/src/compare.py"),
            mutator_name="BinOp",
            lineno=13,
            text="a >= b",
            unified_diff="@@ -5,1 +5,1 @@\n-    a <= b\n+    a >= b\n",
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        ),
        create_mutant_trial(
            source_file=Path("example/src/compare.py"),
            mutator_name="BinOp",
            lineno=9,
            text="a > b",
            unified_diff="@@ -5,1 +5,1 @@\n-    a < b\n+    a > b\n",
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        ),
        create_mutant_trial(
            source_file=Path("example/src/compare.py"),
            mutator_name="BinOp",
            lineno=5,
            text="a != b",
            unified_diff="@@ -5,1 +5,1 @@\n-    a == b\n+    a != b\n",
            found=True,
            reason_code=MutantTrialResult.RC_FOUND,
        ),
    ]


@pytest.fixture()
def testing_results(mutant_trials_augassign, mutant_trials_compare) -> TestingResults:
    return build_testing_results(mutant_trials_augassign, mutant_trials_compare)


def build_testing_results(mutant_trials_augassign, mutant_trials_compare) -> TestingResults:
    return TestingResults(
        mutant_trials=mutant_trials_augassign + mutant_trials_compare,
        summary=TestingSummary(
            trials=100,
            tested=90,
            found=30,
            not_found=50,
            timeout=1,
            errors=9,
        ),
    )


class TestTemplatePath:
    @mock.patch("poodle.reporters.html.Path")
    def test_template_path(self, mock_path: mock.MagicMock):
        assert html.template_path() == mock_path(poodle.__file__).parent.parent / "templates"


class TestStaticFiles:
    def test_static_files(self):
        assert [
            "html-report.js",
            "style.css",
            "poodle.ico",
        ] == html.STATIC_FILES


class TestHtmlReporter:
    @mock.patch("poodle.reporters.html.PackageLoader")
    @mock.patch("poodle.reporters.html.Environment")
    @mock.patch("poodle.reporters.html.shutil")
    @mock.patch("poodle.reporters.html.template_path")
    @mock.patch("poodle.reporters.html.module_data")
    @mock.patch("poodle.reporters.html.local_timestamp")
    @mock.patch("poodle.reporters.html.Path")
    def test_html_reporter(
        self,
        mock_path: mock.MagicMock,
        local_timestamp: mock.MagicMock,
        module_data: mock.MagicMock,
        template_path: mock.MagicMock,
        shutil: mock.MagicMock,
        mock_environment: mock.MagicMock,
        package_loader: mock.MagicMock,
        testing_results: TestingResults,
    ):
        config = PoodleConfigStub(
            reporter_opts={
                "html": {
                    "report_folder": "report",
                    "project_name": "example",
                    "project_version": "1.0.0",
                    "include_found_details": True,
                }
            }
        )
        echo = mock.MagicMock()
        timestamp = "2021-01-01 00:00:00"
        local_timestamp.return_value = timestamp

        common_vars = {
            "project": {
                "name": "example",
                "version": "1.0.0",
            },
            "poodle_version": poodle.__version__,
            "timestamp": timestamp,
        }

        report_folder = mock_path.return_value

        modules = module_data.return_value
        source_file = mock.MagicMock()
        module = mock.MagicMock()
        modules.items.return_value = [(source_file, module)]
        templates_folder = template_path.return_value
        loader = package_loader.return_value
        env = mock_environment.return_value

        html.html_reporter(config, echo, testing_results)

        mock_path.assert_any_call("report")
        module_data.assert_called_once_with(testing_results, config.reporter_opts["html"])
        report_folder.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        shutil.copy2.assert_has_calls(
            [mock.call(templates_folder / file, report_folder / file) for file in html.STATIC_FILES]
        )

        package_loader.assert_called_once_with("poodle")
        mock_environment.assert_called_once_with(loader=loader, autoescape=True)

        env.get_template.assert_has_calls(
            [
                mock.call("html-report-index.html.jinja"),
                mock.call().render(total=testing_results.summary, modules=modules, **common_vars),
                mock.call().render().strip(),
                mock.call("html-report-detail.html.jinja"),
                mock.call().render(modules=modules, **common_vars),
                mock.call().render().strip(),
                mock.call("html-report-module.html.jinja"),
                mock.call().render(source_file=source_file, module=module, **common_vars),
                mock.call().render().strip(),
            ]
        )
        report_folder.__truediv__.assert_has_calls(
            [
                mock.call("index.html"),
                mock.call().write_text(env.get_template.return_value.render.return_value.strip.return_value),
                mock.call("detail.html"),
                mock.call().write_text(env.get_template.return_value.render.return_value.strip.return_value),
                mock.call(module["report_file"]),
                mock.call().write_text(env.get_template.return_value.render.return_value.strip.return_value),
            ]
        )

        index_file = report_folder / "index.html"

        echo.assert_called_once_with(f"HTML Report Generated at {index_file.resolve.return_value}")

    def test_html_reporter_html_options_error(self, testing_results: TestingResults):
        config = PoodleConfigStub(reporter_opts={"html": "not a dictionary"})

        with pytest.raises(TypeError, match=r"^HTML Reporter Options \(reporter_opts\.html\) must be a Dictionary\.$"):
            html.html_reporter(config, mock.MagicMock(), testing_results)

    @mock.patch("poodle.reporters.html.PackageLoader")
    @mock.patch("poodle.reporters.html.Environment")
    @mock.patch("poodle.reporters.html.shutil")
    @mock.patch("poodle.reporters.html.template_path")
    @mock.patch("poodle.reporters.html.module_data")
    @mock.patch("poodle.reporters.html.local_timestamp")
    @mock.patch("poodle.reporters.html.Path")
    def test_html_reporter_defaults(
        self,
        mock_path: mock.MagicMock,
        local_timestamp: mock.MagicMock,
        module_data: mock.MagicMock,
        template_path: mock.MagicMock,
        shutil: mock.MagicMock,
        mock_environment: mock.MagicMock,
        package_loader: mock.MagicMock,
        testing_results: TestingResults,
    ):
        config = PoodleConfigStub(reporter_opts={})
        echo = mock.MagicMock()
        timestamp = "2021-01-01 00:00:00"
        local_timestamp.return_value = timestamp

        common_vars = {
            "project": {
                "name": None,
                "version": None,
            },
            "poodle_version": poodle.__version__,
            "timestamp": timestamp,
        }

        report_folder = mock_path.return_value

        modules = module_data.return_value
        source_file = mock.MagicMock()
        module = mock.MagicMock()
        modules.items.return_value = [(source_file, module)]
        templates_folder = template_path.return_value
        loader = package_loader.return_value
        env = mock_environment.return_value

        html.html_reporter(config, echo, testing_results)

        mock_path.assert_any_call("mutation_reports")
        module_data.assert_called_once_with(testing_results, {})
        report_folder.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        shutil.copy2.assert_has_calls(
            [mock.call(templates_folder / file, report_folder / file) for file in html.STATIC_FILES]
        )

        package_loader.assert_called_once_with("poodle")
        mock_environment.assert_called_once_with(loader=loader, autoescape=True)

        env.get_template.assert_has_calls(
            [
                mock.call("html-report-index.html.jinja"),
                mock.call().render(total=testing_results.summary, modules=modules, **common_vars),
                mock.call().render().strip(),
                mock.call("html-report-detail.html.jinja"),
                mock.call().render(modules=modules, **common_vars),
                mock.call().render().strip(),
                mock.call("html-report-module.html.jinja"),
                mock.call().render(source_file=source_file, module=module, **common_vars),
                mock.call().render().strip(),
            ]
        )

    @mock.patch("poodle.reporters.html.shutil")
    @mock.patch("poodle.reporters.html.Path")
    def test_html_reporter_validate_files(
        self,
        mock_path: mock.MagicMock,
        shutil: mock.MagicMock,  # noqa: ARG002 - Unused method argument
        testing_results,
    ):
        config = PoodleConfigStub(
            reporter_opts={
                "html": {
                    "project_name": "Example Project",
                    "project_version": "0.0.1",
                }
            }
        )
        echo = mock.MagicMock()

        report_folder = mock_path.return_value
        output_files: mock.MagicMock = report_folder.__truediv__.return_value

        html.html_reporter(config, echo, testing_results)

        call_list = output_files.write_text.call_args_list
        for call in call_list:
            page_str = call.args[0]
            assert page_str.startswith("<!DOCTYPE html>")
            assert page_str.endswith("</html>")
            ElementTree.XML(page_str)  # Validate XML Parses Successfully


class TestLocalTimestamp:
    @mock.patch("poodle.reporters.html.datetime")
    def test_local_timestamp(self, mock_datetime: mock.MagicMock):
        dt = datetime.datetime(2021, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
        mock_datetime.datetime.now.return_value = dt
        timestamp = html.local_timestamp()
        assert timestamp == dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


class TestModuleData:
    def test_module_data(self, testing_results, mutant_trials_augassign, mutant_trials_compare):
        html_options = {}
        module_dict = html.module_data(testing_results, html_options)

        augassign_path = Path("example/src/augassign.py")
        compare_path = Path("example/src/compare.py")

        assert module_dict.keys() == {augassign_path, compare_path}

        assert {
            module_dict[augassign_path]["report_file"],
            module_dict[compare_path]["report_file"],
        } == {
            "module-1.html",
            "module-2.html",
        }

        assert module_dict[augassign_path]["trials"] == mutant_trials_augassign
        mutant_trials_compare.sort(key=lambda trial: trial.mutant.lineno)
        assert module_dict[compare_path]["trials"] == mutant_trials_compare

        assert module_dict[augassign_path]["lines"][4] == {
            "lineno": 5,
            "text": "    x += y",
            "trials": [],
            "row_class": "plain",
        }
        assert module_dict[augassign_path]["lines"][14] == {
            "lineno": 15,
            "text": "    x *= y",
            "trials": [mutant_trials_augassign[3]],
            "row_class": "not_found",
        }

        assert module_dict[augassign_path]["summary"] == TestingSummary(
            trials=4,
            tested=4,
            found=2,
            not_found=1,
            timeout=0,
            errors=1,
        )

    def test_module_data_include_found(self, testing_results, mutant_trials_augassign):
        html_options = {"include_found_details": True}
        module_dict = html.module_data(testing_results, html_options)

        augassign_path = Path("example/src/augassign.py")

        assert module_dict[augassign_path]["lines"][14] == {
            "lineno": 15,
            "text": "    x *= y",
            "trials": [mutant_trials_augassign[2], mutant_trials_augassign[3]],
            "row_class": "partial_found",
        }


class TestModuleTrials:
    def test_module_trials(self, mutant_trials_augassign: list, mutant_trials_compare: list):
        module = Path("example/src/augassign.py")
        mutant_trials = mutant_trials_augassign + mutant_trials_compare
        assert list(html.module_trials(module, mutant_trials)) == mutant_trials_augassign


class TestModuleLines:
    def test_module_lines(self):
        module = mock.MagicMock()
        module.read_text.return_value = module_augassign
        lines = list(html.module_lines(module))

        assert lines[0] == {
            "lineno": 1,
            "text": "from __future__ import annotations",
            "trials": [],
            "row_class": "plain",
        }
        assert lines[4] == {
            "lineno": 5,
            "text": "    x += y",
            "trials": [],
            "row_class": "plain",
        }

        module.read_text.assert_called_once_with("utf-8")


class TestModuleTrialsToLines:
    def test_module_add_trials_to_lines(self, mutant_trials_augassign):
        module = mock.MagicMock()
        module.read_text.return_value = module_augassign
        lines = list(html.module_lines(module))

        html.module_add_trials_to_lines(mutant_trials_augassign, lines, include_found=False)

        assert lines[4]["trials"] == []
        assert lines[4]["row_class"] == "plain"

        assert lines[9]["trials"] == [mutant_trials_augassign[1]]
        assert lines[9]["row_class"] == "not_found"

        assert lines[14]["trials"] == [mutant_trials_augassign[3]]
        assert lines[14]["row_class"] == "not_found"

    def test_module_add_trials_to_lines_include_found(self, mutant_trials_augassign):
        module = mock.MagicMock()
        module.read_text.return_value = module_augassign
        lines = list(html.module_lines(module))

        html.module_add_trials_to_lines(mutant_trials_augassign, lines, include_found=True)

        assert lines[4]["trials"] == [mutant_trials_augassign[0]]
        assert lines[4]["row_class"] == "found"

        assert lines[9]["trials"] == [mutant_trials_augassign[1]]
        assert lines[9]["row_class"] == "not_found"

        assert lines[14]["trials"] == [mutant_trials_augassign[2], mutant_trials_augassign[3]]
        assert lines[14]["row_class"] == "partial_found"

    def test_module_add_trials_to_lines_found_first(self, mutant_trials_augassign):
        module = mock.MagicMock()
        module.read_text.return_value = module_augassign
        lines = list(html.module_lines(module))

        html.module_add_trials_to_lines(
            [
                mutant_trials_augassign[2],
                mutant_trials_augassign[3],
            ],
            lines,
            include_found=True,
        )

        assert lines[14]["trials"] == [mutant_trials_augassign[2], mutant_trials_augassign[3]]
        assert lines[14]["row_class"] == "partial_found"

    def test_module_add_trials_to_lines_not_found_first(self, mutant_trials_augassign):
        module = mock.MagicMock()
        module.read_text.return_value = module_augassign
        lines = list(html.module_lines(module))

        html.module_add_trials_to_lines(
            [
                mutant_trials_augassign[3],
                mutant_trials_augassign[2],
            ],
            lines,
            include_found=True,
        )

        assert lines[14]["trials"] == [mutant_trials_augassign[3], mutant_trials_augassign[2]]
        assert lines[14]["row_class"] == "partial_found"


class TestModuleSummary:
    def test_module_summary(self, mutant_trials_augassign: list[MutantTrial]):
        assert html.module_summary(mutant_trials_augassign) == TestingSummary(
            trials=4,
            tested=4,
            found=2,
            not_found=1,
            timeout=0,
            errors=1,
        )
