import importlib
import re
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from poodle import PoodleInputError, cli


class TestCli:
    @pytest.fixture(autouse=True)
    def _setup(self):
        importlib.reload(cli)

    @pytest.fixture()
    def main_process(self):
        with mock.patch("poodle.cli.core.main_process") as main_process:
            yield main_process

    @pytest.fixture()
    def build_config(self):
        with mock.patch("poodle.cli.build_config") as build_config:
            yield build_config

    @pytest.fixture()
    def echo(self):
        with mock.patch("poodle.cli.click.echo") as echo:
            yield echo

    @pytest.fixture()
    def runner(self):
        return CliRunner()

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

    def test_cli(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 0, None, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_sources(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["src", "tests"])
        assert result.exit_code == 0
        build_config.assert_called_with((Path("src"), Path("tests")), None, 0, 0, None, (), ())
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
        build_config.assert_called_with((), Path("pyproject.toml"), 0, 0, None, (), ())
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
        build_config.assert_called_with((), None, 1, 0, None, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_quiet2(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-qq"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 2, 0, None, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_verbose(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-v"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 1, None, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_verbose2(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-vv"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 2, None, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_workers(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["-w", "4"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 0, 4, (), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_exclude(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--exclude", "test_.*"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 0, None, ("test_.*",), ())
        main_process.assert_called_with(build_config.return_value)

    def test_main_only(self, main_process: mock.MagicMock, build_config: mock.MagicMock, runner: CliRunner):
        result = runner.invoke(cli.main, ["--only", "test_.*"])
        assert result.exit_code == 0
        build_config.assert_called_with((), None, 0, 0, None, (), ("test_.*",))
        main_process.assert_called_with(build_config.return_value)

    def test_main_input_error(
        self,
        main_process: mock.MagicMock,
        echo: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        build_config.side_effect = PoodleInputError("bad input")
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 4
        build_config.assert_called()
        echo.assert_called_with(("bad input",))
        main_process.assert_not_called()

    def test_main_keyboard_interrupt(
        self,
        main_process: mock.MagicMock,
        echo: mock.MagicMock,
        build_config: mock.MagicMock,
        runner: CliRunner,
    ):
        main_process.side_effect = KeyboardInterrupt()
        result = runner.invoke(cli.main, [])
        assert result.exit_code == 2
        build_config.assert_called()
        echo.assert_called_with("Aborted due to Keyboard Interrupt!")
        main_process.assert_called_with(build_config.return_value)
