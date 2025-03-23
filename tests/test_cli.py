from __future__ import annotations

import importlib
import re
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from poodle import PoodleInputError, PoodleNoMutantsFoundError, PoodleTestingFailedError, PoodleTrialRunError, cli


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(cli)


@pytest.fixture()
def main_process():
    with mock.patch("poodle.cli.core.main_process") as main_process:
        yield main_process


@pytest.fixture()
def build_config():
    with mock.patch("poodle.cli.build_config") as build_config:
        yield build_config


@pytest.fixture()
def secho():
    with mock.patch("poodle.cli.click.secho") as secho:
        yield secho


@pytest.fixture()
def runner():
    return CliRunner()


class TestCliHelp:
    def test_cli_help(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert result.output.find("Usage: main [OPTIONS] [SOURCES]...") is not None
        assert result.output.find("Poodle Mutation Test Tool.") is not None
        build_config.assert_not_called()
        main_process.assert_not_called()

    def test_cli_help_max_content_width(self, runner: CliRunner):
        with mock.patch("poodle.cli.click.command") as command:
            importlib.reload(cli)
            runner.invoke(cli.main, ["--help"])
        command.assert_called_with(context_settings={"max_content_width": 120})

    def test_cli_help_config_file(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert re.match(r".*-c PATH\s+Configuration File\..*", result.output, flags=re.DOTALL) is not None

    def test_cli_help_quiet(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert re.match(r".*-q\s+Quiet mode: q, qq, or qqq.*", result.output, flags=re.DOTALL) is not None

    def test_cli_help_verbose(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert re.match(r".*-v\s+Verbose mode: v, vv, or vvv.*", result.output, flags=re.DOTALL) is not None

    def test_cli_help_workers(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*-w INTEGER\s+Maximum number of parallel workers\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_exclude(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--exclude TEXT\s+Add a glob exclude file filter\. Multiple allowed\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_only(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--only TEXT\s+Glob pattern for files to mutate\. Multiple allowed\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_report(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--report TEXT\s+Enable reporter by name. Multiple allowed\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_html(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--html PATH\s+Folder name to store HTML report in\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_json(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--json PATH\s+File to create with JSON report\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )

    def test_cli_help_fail_under(self, runner: CliRunner):
        result = runner.invoke(cli.main, ["--help"])
        assert result.exit_code == 0
        assert (
            re.match(
                r".*--fail_under FLOAT\s+Fail if mutation score is under this value\..*",
                result.output,
                flags=re.DOTALL,
            )
            is not None
        )


class TestInputs:
    def assert_build_config_called_with(
        self,
        build_config: mock.MagicMock,
        sources: tuple[Path] = (),  # type: ignore [assignment]
        config_file: Path | None = None,
        quiet: int = 0,
        verbose: int = 0,
        workers: int | None = None,
        exclude: tuple[str] = (),  # type: ignore [assignment]
        only: tuple[str] = (),  # type: ignore [assignment]
        report: tuple[str] = (),  # type: ignore [assignment]
        html: Path | None = None,
        json: Path | None = None,
        fail_under: float | None = None,
    ):
        build_config.assert_called_with(
            sources,
            config_file,
            quiet,
            verbose,
            workers,
            exclude,
            only,
            report,
            html,
            json,
            fail_under,
        )

    def test_cli(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config)
        main_process.assert_called_with(build_config.return_value)

    def test_main_sources(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["src", "tests"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, sources=(Path("src"), Path("tests")))  # type: ignore [arg-type]
        main_process.assert_called_with(build_config.return_value)

    def test_main_sources_not_exist(
        self,
        main_process: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        result = runner.invoke(cli.main, ["not_exist_path"])
        assert result.exit_code > 0
        build_config.assert_not_called()
        main_process.assert_not_called()

    def test_main_config_file(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-c", "pyproject.toml"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, config_file=Path("pyproject.toml"))
        main_process.assert_called_with(build_config.return_value)

    def test_main_config_file_not_exists(
        self,
        main_process: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        result = runner.invoke(cli.main, ["-c", "not_exist_path"])
        assert result.exit_code > 0
        build_config.assert_not_called()
        main_process.assert_not_called()

    def test_main_quiet(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-q"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, quiet=1)
        main_process.assert_called_with(build_config.return_value)

    def test_main_quiet2(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-qq"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, quiet=2)
        main_process.assert_called_with(build_config.return_value)

    def test_main_verbose(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-v"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, verbose=1)
        main_process.assert_called_with(build_config.return_value)

    def test_main_verbose2(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-vv"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, verbose=2)
        main_process.assert_called_with(build_config.return_value)

    def test_main_workers(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-w", "4"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, workers=4)
        main_process.assert_called_with(build_config.return_value)

    def test_main_exclude(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--exclude", "test_.*"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, exclude=("test_.*",))
        main_process.assert_called_with(build_config.return_value)

    def test_main_only(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--only", "test_.*"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, only=("test_.*",))
        main_process.assert_called_with(build_config.return_value)

    def test_main_report(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--report", "json"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, report=("json",))
        main_process.assert_called_with(build_config.return_value)

    def test_main_html(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--html", "html_report"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, html=Path("html_report"))
        main_process.assert_called_with(build_config.return_value)

    def test_main_json(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--json", "summary.json"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, json=Path("summary.json"))
        main_process.assert_called_with(build_config.return_value)

    def test_main_fail_under(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--fail_under", "80"])
        assert result.exit_code == 0
        self.assert_build_config_called_with(build_config, fail_under=80)
        main_process.assert_called_with(build_config.return_value)


class TestErrors:
    def test_main_build_config_input_error(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        build_config.side_effect = PoodleInputError("bad input", "input error")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 4
        build_config.assert_called()
        secho.assert_has_calls(
            [
                mock.call("bad input", fg="red"),
                mock.call("input error", fg="red"),
            ]
        )
        main_process.assert_not_called()

    def test_main_process_testing_failed(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = PoodleTestingFailedError("testing failed", "error message")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 1
        build_config.assert_called()
        secho.assert_has_calls(
            [
                mock.call("testing failed", fg="yellow"),
                mock.call("error message", fg="yellow"),
            ]
        )
        main_process.assert_called_with(build_config.return_value)

    def test_main_process_keyboard_interrupt(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = KeyboardInterrupt()
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 2
        build_config.assert_called()
        secho.assert_called_once_with("Aborted due to Keyboard Interrupt!", fg="yellow")
        main_process.assert_called_with(build_config.return_value)

    def test_main_process_trial_run_error(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = PoodleTrialRunError("testing failed", "error message")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 3
        build_config.assert_called()
        secho.assert_has_calls(
            [
                mock.call("testing failed", fg="red"),
                mock.call("error message", fg="red"),
            ]
        )
        main_process.assert_called_with(build_config.return_value)

    def test_main_process_input_error(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = PoodleInputError("testing failed", "error message")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 4
        build_config.assert_called()
        secho.assert_has_calls(
            [
                mock.call("testing failed", fg="red"),
                mock.call("error message", fg="red"),
            ]
        )
        main_process.assert_called_with(build_config.return_value)

    def test_main_process_no_mutants_error(
        self,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = PoodleNoMutantsFoundError("testing failed", "error message")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 5
        build_config.assert_called()
        secho.assert_has_calls(
            [
                mock.call("testing failed", fg="yellow"),
                mock.call("error message", fg="yellow"),
            ]
        )
        main_process.assert_called_with(build_config.return_value)

    @mock.patch("poodle.cli.traceback")
    def test_main_process_other_error(
        self,
        traceback: mock.MagicMock,
        main_process: mock.MagicMock,
        secho: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = Exception()
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 3
        build_config.assert_called()
        secho.assert_any_call("Aborted due to Internal Error!", fg="red")
        secho.assert_any_call(traceback.format_exc.return_value, fg="red")
        main_process.assert_called_with(build_config.return_value)
