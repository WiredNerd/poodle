from __future__ import annotations

import importlib
import logging
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest
from wcmatch import glob

from poodle import PoodleInputError, config, tomllib


@pytest.fixture(autouse=True)
def _test_wrapper():
    importlib.reload(config)
    config.poodle_config = None
    yield
    importlib.reload(config)


@pytest.fixture()
def mock_logging():
    with mock.patch("poodle.config.logging") as mock_logging:
        yield mock_logging


@pytest.fixture()
def get_option_from_config():
    with mock.patch("poodle.config.get_option_from_config") as get_option_from_config:
        yield get_option_from_config


def test_defaults():
    importlib.reload(config)

    assert config.default_source_folders == [Path("src"), Path("lib")]

    assert config.default_log_format == "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
    assert config.default_log_level == logging.WARN

    assert config.default_file_flags == glob.GLOBSTAR | glob.NODIR
    assert config.default_file_filters == ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]

    assert config.default_file_copy_flags == glob.GLOBSTAR | glob.NODIR
    assert config.default_file_copy_filters == ["__pycache__/**"]
    assert config.default_work_folder == Path(".poodle-temp")

    assert config.default_min_timeout == 10
    assert config.default_timeout_multiplier == 10
    assert config.default_runner == "command_line"

    assert config.default_reporters == ["summary", "not_found"]


class TestMaxWorkers:
    @mock.patch("poodle.config.os")
    def test_default_max_workers_affinity(self, os_mock):
        os_mock.sched_getaffinity.return_value = [1, 2, 3, 4, 5, 6]
        os_mock.cpu_count.return_value = 8
        assert config.default_max_workers() == 5
        os_mock.sched_getaffinity.assert_called_with(0)
        os_mock.cpu_count.assert_not_called()

    @mock.patch("poodle.config.os")
    def test_default_max_workers_cpu(self, os_mock):
        del os_mock.sched_getaffinity
        os_mock.cpu_count.return_value = 2
        assert config.default_max_workers() == 1
        os_mock.cpu_count.assert_called()

    @mock.patch("poodle.config.os")
    def test_default_max_workers_cpu_1(self, os_mock):
        del os_mock.sched_getaffinity
        os_mock.cpu_count.return_value = 1
        assert config.default_max_workers() == 1
        os_mock.cpu_count.assert_called()

    @mock.patch("poodle.config.os")
    def test_default_max_workers_neither(self, os_mock):
        del os_mock.sched_getaffinity
        os_mock.cpu_count.return_value = None
        assert config.default_max_workers() == 1
        os_mock.cpu_count.assert_called()


class TestBuildConfig:
    @pytest.fixture()
    def mock_os(self):
        with mock.patch("poodle.config.os") as mock_os:
            yield mock_os

    @pytest.fixture()
    def get_reporters(self):
        with mock.patch("poodle.config.get_reporters") as get_reporters:
            yield get_reporters

    @pytest.fixture()
    def get_config_file_path(self):
        with mock.patch("poodle.config.get_config_file_path") as get_config_file_path:
            yield get_config_file_path

    @pytest.fixture()
    def get_config_file_data(self):
        with mock.patch("poodle.config.get_config_file_data") as get_config_file_data:
            yield get_config_file_data

    @pytest.fixture()
    def get_project_info(self):
        with mock.patch("poodle.config.get_project_info") as get_project_info:
            get_project_info.return_value = ("example", "1,2,3")
            yield get_project_info

    @pytest.fixture()
    def get_cmd_line_log_level(self):
        with mock.patch("poodle.config.get_cmd_line_log_level") as get_cmd_line_log_level:
            yield get_cmd_line_log_level

    @pytest.fixture()
    def get_source_folders(self):
        with mock.patch("poodle.config.get_source_folders") as get_source_folders:
            yield get_source_folders

    @pytest.fixture()
    def get_str_from_config(self):
        with mock.patch("poodle.config.get_str_from_config") as get_str_from_config:
            yield get_str_from_config

    @pytest.fixture()
    def get_str_list_from_config(self):
        with mock.patch("poodle.config.get_str_list_from_config") as get_str_list_from_config:
            yield get_str_list_from_config

    @pytest.fixture()
    def get_path_from_config(self):
        with mock.patch("poodle.config.get_path_from_config") as get_path_from_config:
            yield get_path_from_config

    @pytest.fixture()
    def get_dict_from_config(self):
        with mock.patch("poodle.config.get_dict_from_config") as get_dict_from_config:
            yield get_dict_from_config

    @pytest.fixture()
    def get_bool_from_config(self):
        with mock.patch("poodle.config.get_bool_from_config") as get_bool_from_config:
            yield get_bool_from_config

    @pytest.fixture()
    def get_int_from_config(self):
        with mock.patch("poodle.config.get_int_from_config") as get_int_from_config:
            yield get_int_from_config

    @pytest.fixture()
    def get_float_from_config(self):
        with mock.patch("poodle.config.get_float_from_config") as get_float_from_config:
            yield get_float_from_config

    @pytest.fixture()
    def get_any_from_config(self):
        with mock.patch("poodle.config.get_any_from_config") as get_any_from_config:
            yield get_any_from_config

    @pytest.fixture()
    def get_any_list_from_config(self):
        with mock.patch("poodle.config.get_any_list_from_config") as get_any_list_from_config:
            yield get_any_list_from_config

    @pytest.fixture()
    def get_cmd_line_echo_enabled(self):
        with mock.patch("poodle.config.get_cmd_line_echo_enabled") as get_cmd_line_echo_enabled:
            yield get_cmd_line_echo_enabled

    @pytest.fixture()
    def default_max_workers(self):
        with mock.patch("poodle.config.default_max_workers") as default_max_workers:
            yield default_max_workers

    @pytest.fixture()
    def _setup_build_config_mocks(
        self,
        get_cmd_line_echo_enabled: mock.MagicMock,
        get_any_list_from_config: mock.MagicMock,
        get_any_from_config: mock.MagicMock,
        get_int_from_config: mock.MagicMock,
        get_bool_from_config: mock.MagicMock,
        get_dict_from_config: mock.MagicMock,
        get_path_from_config: mock.MagicMock,
        get_str_list_from_config: mock.MagicMock,
        get_str_from_config: mock.MagicMock,
        get_source_folders: mock.MagicMock,
        get_cmd_line_log_level: mock.MagicMock,
        get_project_info: mock.MagicMock,
        get_config_file_data: mock.MagicMock,
        get_config_file_path: mock.MagicMock,
        get_reporters: mock.MagicMock,
        mock_os: mock.MagicMock,
        mock_logging: mock.MagicMock,
    ):
        get_cmd_line_echo_enabled.reset_mock()
        get_any_list_from_config.reset_mock()
        get_any_from_config.reset_mock()
        get_int_from_config.reset_mock()
        get_bool_from_config.reset_mock()
        get_dict_from_config.reset_mock()
        get_path_from_config.reset_mock()
        get_str_list_from_config.reset_mock()
        get_str_from_config.reset_mock()
        get_source_folders.reset_mock()
        get_cmd_line_log_level.reset_mock()
        get_project_info.reset_mock()
        get_config_file_data.reset_mock()
        get_config_file_path.reset_mock()
        get_reporters.reset_mock()
        mock_os.reset_mock()
        mock_logging.reset_mock()

    def build_config_with(
        self,
        cmd_sources: tuple[Path] = (Path("src"),),
        cmd_config_file: Path | None = None,
        cmd_quiet: int = 0,
        cmd_verbose: int = 0,
        cmd_max_workers: int | None = None,
        cmd_excludes: tuple[str] = (),  # type: ignore[assignment]
        cmd_only_files: tuple[str] = (),  # type: ignore[assignment]
        cmd_report: tuple[str] = (),  # type: ignore[assignment]
        cmd_html: Path | None = None,
        cmd_json: Path | None = None,
        cmd_fail_under: float | None = None,
    ):
        return config.build_config(
            cmd_sources,
            cmd_config_file,
            cmd_quiet,
            cmd_verbose,
            cmd_max_workers,
            cmd_excludes,
            cmd_only_files,
            cmd_report,
            cmd_html,
            cmd_json,
            cmd_fail_under,
        )

    def test_build_config_project_info(self, get_project_info: mock.MagicMock):
        get_project_info.return_value = ("example", "1.2.3")
        config_data = self.build_config_with()
        assert config_data.project_name == "example"
        assert config_data.project_version == "1.2.3"

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_config_file(self, get_config_file_path, get_config_file_data):
        config_data = self.build_config_with(cmd_config_file=Path("config.toml"))
        assert config_data.config_file == get_config_file_path.return_value
        get_config_file_path.assert_called_with(Path("config.toml"))
        get_config_file_data.assert_called_with(get_config_file_path.return_value)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_source_folders(self, get_source_folders, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(cmd_sources=(Path("source"),))
        assert config_data.source_folders == get_source_folders.return_value
        get_source_folders.assert_called_with((Path("source"),), config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_only_files(self, get_str_list_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(cmd_only_files=("example.py",))
        assert config_data.only_files == get_str_list_from_config.return_value
        get_str_list_from_config.assert_any_call(
            "only_files",
            config_file_data,
            default=[],
            command_line=("example.py",),
        )

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_file_flags(self, get_int_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.file_flags == get_int_from_config.return_value
        get_int_from_config.assert_any_call("file_flags", config_file_data, default=config.default_file_flags)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_file_filters(self, get_str_list_from_config):
        get_str_list_from_config.return_value = ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]
        config_data = self.build_config_with(cmd_excludes=("notcov.py",))
        assert config_data.file_filters == ["test_*.py", "*_test.py", "poodle_config.py", "setup.py", "notcov.py"]

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_file_copy_flags(self, get_int_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.file_copy_flags == get_int_from_config.return_value
        get_int_from_config.assert_any_call("file_copy_flags", config_file_data, default=config.default_file_copy_flags)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_file_copy_filters(self, get_str_list_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.file_copy_filters == get_str_list_from_config.return_value
        get_str_list_from_config.assert_any_call(
            "file_copy_filters",
            config_file_data,
            default=config.default_file_copy_filters,
        )

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_work_folder(self, get_path_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.work_folder == get_path_from_config.return_value
        get_path_from_config.assert_any_call("work_folder", config_file_data, default=config.default_work_folder)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_max_workers(self, get_int_from_config, default_max_workers, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        default_max_workers.return_value = 5
        config_data = self.build_config_with(cmd_max_workers=3)
        assert config_data.max_workers == get_int_from_config.return_value
        get_int_from_config.assert_any_call("max_workers", config_file_data, default=5, command_line=3)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_logging(
        self,
        get_str_from_config,
        get_any_from_config,
        mock_logging,
        get_config_file_data,
        get_cmd_line_log_level,
    ):
        config_file_data = get_config_file_data.return_value
        get_str_from_config.return_value = "example log format"
        get_any_from_config.return_value = logging.CRITICAL

        config_data = self.build_config_with(cmd_quiet=1, cmd_verbose=2)
        assert config_data.log_format == "example log format"
        assert config_data.log_level == logging.CRITICAL
        get_str_from_config.assert_any_call("log_format", config_file_data, default=config.default_log_format)
        get_any_from_config.assert_any_call(
            "log_level",
            config_file_data,
            default=config.default_log_level,
            command_line=get_cmd_line_log_level.return_value,
        )
        mock_logging.basicConfig.assert_called_once_with(format="example log format", level=logging.CRITICAL)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_echo_enabled(self, get_bool_from_config, get_cmd_line_echo_enabled, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(cmd_quiet=1)
        assert config_data.echo_enabled == get_bool_from_config.return_value
        get_bool_from_config.assert_any_call(
            "echo_enabled",
            config_file_data,
            default=True,
            command_line=get_cmd_line_echo_enabled.return_value,
        )
        get_cmd_line_echo_enabled.assert_called_once_with(1)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_echo_no_color(self, get_bool_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.echo_no_color == get_bool_from_config.return_value
        get_bool_from_config.assert_any_call("echo_no_color", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_mutator_opts(self, get_dict_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.mutator_opts == get_dict_from_config.return_value
        get_dict_from_config.assert_any_call("mutator_opts", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_skip_mutators(self, get_str_list_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.skip_mutators == get_str_list_from_config.return_value
        get_str_list_from_config.assert_any_call("skip_mutators", config_file_data, default=[])

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_add_mutators(self, get_any_list_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.add_mutators == get_any_list_from_config.return_value
        get_any_list_from_config.assert_any_call("add_mutators", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_min_timeout(self, get_int_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.min_timeout == get_int_from_config.return_value
        get_int_from_config.assert_any_call("min_timeout", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_min_timeout_default(self, get_int_from_config):
        get_int_from_config.return_value = None
        config_data = self.build_config_with()
        assert config_data.min_timeout == config.default_min_timeout

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_timeout_multiplier(self, get_int_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.timeout_multiplier == get_int_from_config.return_value
        get_int_from_config.assert_any_call("timeout_multiplier", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_timeout_multiplier_default(self, get_int_from_config):
        get_int_from_config.return_value = None
        config_data = self.build_config_with()
        assert config_data.timeout_multiplier == config.default_timeout_multiplier

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_runner(self, get_str_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.runner == get_str_from_config.return_value
        get_str_from_config.assert_any_call("runner", config_file_data, default=config.default_runner)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_runner_opts(self, get_dict_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with()
        assert config_data.runner_opts == get_dict_from_config.return_value
        get_dict_from_config.assert_any_call("runner_opts", config_file_data)

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_reporters(self, get_reporters, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(
            cmd_report=("myreporter",),
            cmd_html=Path("html"),
            cmd_json=Path("json"),
        )
        assert config_data.reporters == get_reporters.return_value
        get_reporters.assert_called_once_with(config_file_data, ("myreporter",), Path("html"), Path("json"))

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_reporter_opts(self, get_dict_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(
            cmd_html=Path("html"),
            cmd_json=Path("json"),
        )
        assert config_data.reporter_opts == get_dict_from_config.return_value
        get_dict_from_config.assert_any_call(
            "reporter_opts",
            config_file_data,
            command_line={"json_report_file": Path("json"), "html": {"report_folder": Path("html")}},
        )

    @pytest.mark.usefixtures("_setup_build_config_mocks")
    def test_build_config_fail_under(self, get_float_from_config, get_config_file_data):
        config_file_data = get_config_file_data.return_value
        config_data = self.build_config_with(cmd_fail_under=50)
        assert config_data.fail_under == get_float_from_config.return_value
        get_float_from_config.assert_any_call("fail_under", config_file_data, command_line=50)

    @mock.patch("poodle.config.get_config_file_data")
    @mock.patch("poodle.config.get_project_info")
    def test_build_config_defaults(self, get_project_info, get_config_file_data):
        get_config_file_data.return_value = {}
        get_project_info.return_value = (None, None)

        assert config.build_config(
            cmd_sources=(),
            cmd_config_file=None,
            cmd_quiet=0,
            cmd_verbose=0,
            cmd_max_workers=None,
            cmd_excludes=(),
            cmd_only_files=(),
            cmd_report=(),
            cmd_html=None,
            cmd_json=None,
            cmd_fail_under=None,
        ) == config.PoodleConfig(
            project_name=None,
            project_version=None,
            config_file=Path("pyproject.toml"),
            source_folders=[Path("src")],
            only_files=[],
            file_flags=config.default_file_flags,
            file_filters=config.default_file_filters,
            file_copy_flags=config.default_file_copy_flags,
            file_copy_filters=config.default_file_copy_filters,
            work_folder=Path(".poodle-temp"),
            max_workers=config.default_max_workers(),
            log_format=config.default_log_format,
            log_level=logging.WARN,
            echo_enabled=True,
            echo_no_color=None,
            mutator_opts={},
            skip_mutators=[],
            add_mutators=[],
            min_timeout=10,
            timeout_multiplier=10,
            runner="command_line",
            runner_opts={},
            reporters=["summary", "not_found"],
            reporter_opts={},
            fail_under=None,
        )


class TestGetReporters:
    @pytest.fixture()
    def get_str_list_from_config(self):
        with mock.patch("poodle.config.get_str_list_from_config") as get_str_list_from_config:
            yield get_str_list_from_config

    def test_get_reporters(self, get_str_list_from_config):
        config_file_data = mock.MagicMock()
        get_str_list_from_config.return_value = ["example1", "example2"]
        assert config.get_reporters(config_file_data, ("example3",), None, None) == ["example1", "example2", "example3"]

    def test_get_reporters_html(self, get_str_list_from_config):
        config_file_data = mock.MagicMock()
        get_str_list_from_config.return_value = ["example1", "example2"]
        assert config.get_reporters(config_file_data, ("example3",), Path("output"), None) == [
            "example1",
            "example2",
            "example3",
            "html",
        ]

    def test_get_reporters_json(self, get_str_list_from_config):
        config_file_data = mock.MagicMock()
        get_str_list_from_config.return_value = ["example1", "example2"]
        assert config.get_reporters(config_file_data, ("example3",), None, Path("output")) == [
            "example1",
            "example2",
            "example3",
            "json",
        ]

    def test_get_reporters_all(self, get_str_list_from_config):
        config_file_data = mock.MagicMock()
        get_str_list_from_config.return_value = ["example1", "example2"]
        assert config.get_reporters(config_file_data, ("example3",), Path("output"), Path("output")) == [
            "example1",
            "example2",
            "example3",
            "html",
            "json",
        ]


class TestGetCommandLineLoggingOptions:
    @pytest.mark.parametrize(
        ("cmd_quiet", "cmd_verbose", "expected"),
        [
            (0, 0, None),
            (1, 0, logging.WARN),
            (2, 0, logging.ERROR),
            (3, 0, logging.CRITICAL),
            (4, 0, logging.CRITICAL),
            (1, 1, logging.WARN),
            (0, 1, logging.INFO),
            (0, 2, logging.DEBUG),
            (0, 3, logging.NOTSET),
            (0, 4, logging.NOTSET),
        ],
    )
    def test_get_cmd_line_log_level(self, cmd_quiet, cmd_verbose, expected):
        assert config.get_cmd_line_log_level(cmd_quiet, cmd_verbose) == expected

    @pytest.mark.parametrize(
        ("cmd_quiet", "expected"),
        [
            (0, None),
            (1, False),
            (2, False),
        ],
    )
    def test_get_cmd_line_echo_enabled(self, cmd_quiet, expected):
        assert config.get_cmd_line_echo_enabled(cmd_quiet) is expected


class TestGetConfigFilePath:
    def setup_mock_path(self, mock_path, config_is_file, poodle_is_file, pyproject_is_file):
        mock_path.config_file_path.is_file.return_value = config_is_file
        mock_path.poodle_toml_path.is_file.return_value = poodle_is_file
        mock_path.pyproject_toml_path.is_file.return_value = pyproject_is_file

        def get_path(filename):
            if filename == "config.toml":
                return mock_path.config_file_path
            if filename == "poodle.toml":
                return mock_path.poodle_toml_path
            if filename == "pyproject.toml":
                return mock_path.pyproject_toml_path
            return None

        mock_path.side_effect = get_path

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_cmd_line(self, mock_path):
        self.setup_mock_path(mock_path, True, True, True)
        path_config = mock.MagicMock()
        path_config.is_file.return_value = True
        assert config.get_config_file_path(path_config) == path_config

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_cmd_line_not_found(self, mock_path):
        self.setup_mock_path(mock_path, False, True, True)
        path_config = mock.MagicMock()
        path_config.is_file.return_value = False
        path_config.__repr__ = lambda _: "config.toml"
        with pytest.raises(PoodleInputError, match="^Config file not found: 'config.toml'$"):
            config.get_config_file_path(path_config)

    @mock.patch("poodle.config.Path")
    @mock.patch("poodle.config.poodle_config")
    def test_get_config_file_path_poodle_config(self, poodle_config, mock_path):
        self.setup_mock_path(mock_path, True, False, False)
        poodle_config.config_file = "config.toml"
        assert config.get_config_file_path(None) == mock_path.config_file_path

    @mock.patch("poodle.config.Path")
    @mock.patch("poodle.config.poodle_config")
    def test_get_config_file_path_poodle_config_err(self, poodle_config, mock_path):
        self.setup_mock_path(mock_path, False, False, False)
        poodle_config.config_file = "config.toml"
        mock_path.config_file_path.__repr__ = lambda _: "config.toml"
        with pytest.raises(PoodleInputError, match="^config_file not found: 'config.toml'$"):
            config.get_config_file_path(None)

    @mock.patch("poodle.config.Path")
    @mock.patch("poodle.config.poodle_config")
    def test_get_config_file_path_poodle(self, poodle_config, mock_path):
        del poodle_config.config_file
        self.setup_mock_path(mock_path, False, True, True)
        assert config.get_config_file_path(None) == mock_path.poodle_toml_path

    @mock.patch("poodle.config.Path")
    @mock.patch("poodle.config.poodle_config")
    def test_get_config_file_path_pyproject(self, poodle_config, mock_path):
        del poodle_config.config_file
        self.setup_mock_path(mock_path, False, False, True)
        assert config.get_config_file_path(None) == mock_path.pyproject_toml_path

    @mock.patch("poodle.config.Path")
    @mock.patch("poodle.config.poodle_config")
    def test_get_config_file_path_none(self, poodle_config, mock_path):
        del poodle_config.config_file
        self.setup_mock_path(mock_path, False, False, False)
        assert config.get_config_file_path(None) is None


class TestGetConfigFileData:
    def test_get_config_file_data_no_file(self):
        assert config.get_config_file_data(None) == {}

    @mock.patch("poodle.config.get_config_file_data_toml")
    def test_get_config_file_data(self, get_config_file_data_toml):
        get_config_file_data_toml.return_value = {"test": "value"}
        assert config.get_config_file_data(Path("config.toml")) == {"test": "value"}
        get_config_file_data_toml.assert_called_with(Path("config.toml"))

    def test_get_config_file_data_invalid(self):
        with pytest.raises(PoodleInputError, match="^Config file type not supported: --config_file='config.txt'$"):
            config.get_config_file_data(Path("config.txt"))


class TestGetProjectInfo:
    def test_get_project_info_no_file(self):
        assert config.get_project_info(None) == ("", "")

    @mock.patch("poodle.config.get_project_info_toml")
    def test_get_project_info_data(self, get_project_info_toml):
        get_project_info_toml.return_value = ("example", "1.2.3")
        assert config.get_project_info(Path("config.toml")) == ("example", "1.2.3")
        get_project_info_toml.assert_called_with(Path("config.toml"))

    def test_get_project_info_invalid(self):
        with pytest.raises(PoodleInputError, match="^Config file type not supported: --config_file='config.txt'$"):
            config.get_project_info(Path("config.txt"))


config_toml_poodle = """
[project]
name = "example"
version = "1.2.3"
[poodle]
test = "value1"
"""

config_toml_tool_poodle = """
[tool.poodle]
test = "value2"
"""

config_toml_no_data = """
[project]
test = "value3"
"""


class TestGetConfigFileDataToml:
    def test_get_config_file_data_toml_poodle(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_poodle, encoding="utf-8"))
        assert config.get_config_file_data_toml(file_path) == {"test": "value1"}
        file_path.open.assert_called_with(mode="rb")

    def test_get_config_file_data_toml_tool_poodle(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_tool_poodle, encoding="utf-8"))
        assert config.get_config_file_data_toml(file_path) == {"test": "value2"}
        file_path.open.assert_called_with(mode="rb")

    def test_get_config_file_data_toml_no_data(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_no_data, encoding="utf-8"))
        assert config.get_config_file_data_toml(file_path) == {}
        file_path.open.assert_called_with(mode="rb")

    @mock.patch("poodle.config.tomllib.load")
    def test_get_config_file_data_toml_decode_error(self, tomllib_load):
        tomllib_load.side_effect = tomllib.TOMLDecodeError("Could not Decode", "Bad data")
        config_file = mock.MagicMock()
        with pytest.raises(PoodleInputError) as err:
            config.get_config_file_data_toml(config_file)
        assert err.value.args == (
            f"Error decoding toml file: {config_file}",
            "Could not Decode",
            "Bad data",
        )


class TestGetProjectInfoToml:
    def test_get_project_info_toml_poodle(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_poodle, encoding="utf-8"))
        assert config.get_project_info_toml(file_path) == ("example", "1.2.3")
        file_path.open.assert_called_with(mode="rb")

    def test_get_project_info_toml_no_data(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_no_data, encoding="utf-8"))
        assert config.get_project_info_toml(file_path) == ("", "")
        file_path.open.assert_called_with(mode="rb")

    @mock.patch("poodle.config.tomllib.load")
    def test_get_project_info_data_decode_error(self, tomllib_load):
        tomllib_load.side_effect = tomllib.TOMLDecodeError("Could not Decode", "Bad data")
        config_file = mock.MagicMock()
        assert config.get_project_info_toml(config_file) == ("", "")


class TestGetSourceFolders:
    @mock.patch("poodle.config.get_path_list_from_config")
    def test_get_source_folders(self, get_path_list_from_config):
        path_project = mock.MagicMock()
        path_project.is_dir.return_value = True

        get_path_list_from_config.return_value = [path_project]

        path_src = mock.MagicMock()
        path_src.is_dir.return_value = False
        path_lib = mock.MagicMock()
        path_lib.is_dir.return_value = True
        config.default_source_folders = [path_src, path_lib]

        assert config.get_source_folders((Path("src"),), {"source_folders": []}) == [path_project]

        get_path_list_from_config.assert_called_with(
            option_name="source_folders",
            config_data={"source_folders": []},
            command_line=(Path("src"),),
            default=[path_lib],
        )

        path_project.is_dir.assert_called()
        path_src.is_dir.assert_called()
        path_lib.is_dir.assert_called()

    @mock.patch("poodle.config.get_path_list_from_config")
    def test_get_source_folders_not_found(self, get_path_list_from_config):
        get_path_list_from_config.return_value = []
        with pytest.raises(PoodleInputError, match="^No source folder found to mutate.$"):
            config.get_source_folders((), {})

    @mock.patch("poodle.config.get_path_list_from_config")
    def test_get_source_folders_not_folder(self, get_path_list_from_config):
        path_project = mock.MagicMock()
        path_project.is_dir.return_value = False
        path_project.__repr__ = lambda _: "project"

        get_path_list_from_config.return_value = [path_project]

        with pytest.raises(PoodleInputError, match="Source 'project' must be a folder."):
            config.get_source_folders((), {})


class TestGetBoolFromConfig:
    @pytest.mark.parametrize(("expected"), [(True), (False)])
    def test_default(self, expected, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_bool_from_config(
                option_name="test_option",
                config_data={"test_option": not expected},
                command_line=not expected,
                default=expected,
            )
            == expected
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": not expected},
            command_line=not expected,
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_bool_from_config(
                option_name="test_option",
                config_data={"test_option": True},
            )
            is None
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": True},
            command_line=None,
        )

    @pytest.mark.parametrize(
        ("option", "default", "expected"),
        [
            (True, False, True),
            (False, True, False),
            ("true", False, True),
            ("False", True, False),
            (None, True, True),
            (None, False, False),
        ],
    )
    def test_values(self, option, default, expected, get_option_from_config):
        get_option_from_config.return_value = (option, None)

        assert (
            config.get_bool_from_config(
                option_name="test_option",
                config_data={},
                default=default,
            )
            == expected
        )


class TestGetPathFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=Path("command_line_value"),
            default=Path("default_value"),
        ) == Path("default_value")

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=Path("command_line_value"),
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            default=Path("default_value"),
        ) == Path("default_value")

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=None,
        )

    def test_string(self, get_option_from_config):
        get_option_from_config.return_value = ("return_value", "Source Name")

        assert config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == Path("return_value")

    def test_empty_string(self, get_option_from_config):
        get_option_from_config.return_value = ("", "Source Name")

        assert (
            config.get_path_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
                command_line="command_line_value",
                default=Path("default_value"),
            )
            == Path()
        )

    def test_not_path(self, get_option_from_config):
        get_option_from_config.return_value = (123, "Source Name")

        with pytest.raises(PoodleInputError, match=r"^test_option from Source Name must be a valid StrPath$"):
            config.get_path_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=Path("default_value"),
            )


class TestGetPathListFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=[Path("command_line_value")],
            default=[Path("default_value")],
        ) == [Path("default_value")]

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=[Path("command_line_value")],
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert (
            config.get_path_list_from_config(
                option_name="test_option",
                config_data={"test_option": [Path("config_file_value")]},
            )
            == []
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=(),
        )

    def test_path(self, get_option_from_config):
        get_option_from_config.return_value = (Path("return_value"), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=[Path("default_value")],
        ) == [Path("return_value")]

    def test_string(self, get_option_from_config):
        get_option_from_config.return_value = ("return_value", "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=[Path("default_value")],
        ) == [Path("return_value")]

    def test_string_empty(self, get_option_from_config):
        get_option_from_config.return_value = ("", "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=[Path("default_value")],
        ) == [Path()]

    def test_path_list(self, get_option_from_config):
        get_option_from_config.return_value = ((Path("return_value"), Path("other_value")), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=[Path("default_value")],
        ) == [Path("return_value"), Path("other_value")]

    def test_string_list(self, get_option_from_config):
        get_option_from_config.return_value = (("return_value", "other_value"), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=[Path("default_value")],
        ) == [Path("return_value"), Path("other_value")]

    def test_empty_list(self, get_option_from_config):
        get_option_from_config.return_value = ([], "Source Name")
        assert (
            config.get_path_list_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=[Path("default_value")],
            )
            == []
        )

    def test_not_iterable(self, get_option_from_config):
        get_option_from_config.return_value = (123, "Source Name")
        with pytest.raises(
            PoodleInputError,
            match=r"^test_option from Source Name must be a valid Iterable\[StrPath\]$",
        ):
            config.get_path_list_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=[Path("default_value")],
            )

    def test_not_path(self, get_option_from_config):
        get_option_from_config.return_value = ([123], "Source Name")
        with pytest.raises(
            PoodleInputError,
            match=r"^test_option from Source Name must be a valid Iterable\[StrPath\]$",
        ):
            config.get_path_list_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=[Path("default_value")],
            )


class TestGetAnyFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_any_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
                command_line="4",
                default=5.5,
            )
            == 5.5
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line="4",
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_any_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
            )
            is None
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line=None,
        )

    def test_return_value(self, get_option_from_config):
        get_option_from_config.return_value = (False, "Source Name")

        assert (
            config.get_any_from_config(
                option_name="test_option",
                config_data={"test_option": "3"},
                command_line="4",
                default="5",
            )
            is False
        )


class TestGetAnyListFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert config.get_any_list_from_config(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
            default=["default_value"],
        ) == ["default_value"]

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert (
            config.get_any_list_from_config(
                option_name="test_option",
                config_data={"test_option": ["config_file_value"]},
            )
            == []
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=(),
        )

    def test_string(self, get_option_from_config):
        get_option_from_config.return_value = ("return_value", "Source Name")
        assert config.get_any_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["return_value"]

    def test_iterable(self, get_option_from_config):
        get_option_from_config.return_value = (iter(["return_value", "other_value"]), "Source Name")
        assert config.get_any_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["return_value", "other_value"]

    def test_tuple(self, get_option_from_config):
        get_option_from_config.return_value = (("return_value", "other_value"), "Source Name")
        assert config.get_any_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["return_value", "other_value"]

    def test_int(self, get_option_from_config):
        get_option_from_config.return_value = (3, "Source Name")
        assert config.get_any_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == [3]


class TestGetIntFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_int_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
                command_line=4,
                default=5,
            )
            == 5
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line=4,
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_int_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
            )
            is None
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line=None,
        )

    def test_str_to_int(self, get_option_from_config):
        get_option_from_config.return_value = ("5", "Source Name")

        assert (
            config.get_int_from_config(
                option_name="test_option",
                config_data={"test_option": "3"},
                command_line="4",
                default="5",
            )
            == 5
        )

    def test_convert_error(self, get_option_from_config):
        get_option_from_config.return_value = ("a", "Source Name")

        with pytest.raises(ValueError, match="^test_option from Source Name must be a valid int$"):
            config.get_int_from_config(
                option_name="test_option",
                config_data={"test_option": "3"},
                command_line="4",
                default="5",
            )


class TestGetFloatFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_float_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
                command_line=4,
                default=5,
            )
            == 5.0
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line=4,
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_float_from_config(
                option_name="test_option",
                config_data={"test_option": 3},
            )
            is None
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": 3},
            command_line=None,
        )

    def test_str_to_float(self, get_option_from_config):
        get_option_from_config.return_value = ("5", "Source Name")

        assert (
            config.get_float_from_config(
                option_name="test_option",
                config_data={"test_option": "3"},
                command_line="4",
                default="5",
            )
            == 5
        )

    def test_convert_error(self, get_option_from_config):
        get_option_from_config.return_value = ("a", "Source Name")

        with pytest.raises(ValueError, match="^test_option from Source Name must be a valid float$"):
            config.get_float_from_config(
                option_name="test_option",
                config_data={"test_option": "3"},
                command_line="4",
                default="5",
            )


class TestGetStrFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_str_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
                command_line="command_line_value",
                default="default_value",
            )
            == "default_value"
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)

        assert (
            config.get_str_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
            )
            == ""
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        )

    def test_string(self, get_option_from_config):
        get_option_from_config.return_value = ("return_value", "Source Name")

        assert (
            config.get_str_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
                command_line="command_line_value",
                default="default_value",
            )
            == "return_value"
        )

    def test_empty_string(self, get_option_from_config):
        get_option_from_config.return_value = ("", "Source Name")

        assert (
            config.get_str_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
                command_line="command_line_value",
                default="default_value",
            )
            == ""
        )

    def test_convert(self, get_option_from_config):
        get_option_from_config.return_value = (Path("source.py"), "Source Name")

        assert (
            config.get_str_from_config(
                option_name="test_option",
                config_data={"test_option": "config_file_value"},
                command_line="command_line_value",
                default="default_value",
            )
            == "source.py"
        )


class TestGetStrListFromConfig:
    def test_default(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
            default=["default_value"],
        ) == ["default_value"]

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
        )

    def test_default_inputs(self, get_option_from_config):
        get_option_from_config.return_value = (None, None)
        assert (
            config.get_str_list_from_config(
                option_name="test_option",
                config_data={"test_option": ["config_file_value"]},
            )
            == []
        )

        get_option_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=(),
        )

    def test_string(self, get_option_from_config):
        get_option_from_config.return_value = ("return_value", "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["return_value"]

    def test_string_empty(self, get_option_from_config):
        get_option_from_config.return_value = ("", "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == [""]

    def test_string_list(self, get_option_from_config):
        get_option_from_config.return_value = (("return_value", "other_value"), "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["return_value", "other_value"]

    def test_string_list_convert(self, get_option_from_config):
        get_option_from_config.return_value = ((Path("output.txt"),), "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={},
            command_line=[],
            default=["default_value"],
        ) == ["output.txt"]

    def test_string_list_empty(self, get_option_from_config):
        get_option_from_config.return_value = ([], "Source Name")
        assert (
            config.get_str_list_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=["default_value"],
            )
            == []
        )

    def test_type_error(self, get_option_from_config):
        get_option_from_config.return_value = (123, "Source Name")
        with pytest.raises(PoodleInputError, match=r"^test_option from Source Name must be a valid Iterable\[str\]$"):
            config.get_str_list_from_config(
                option_name="test_option",
                config_data={},
                command_line=[],
                default=["default_value"],
            )


class TestGetOptionFromConfig:
    def test_get_command_line_value(self):
        assert config.get_option_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
        ) == ("command_line_value", "Command Line")

    def test_get_poodle_config_value(self):
        config.poodle_config = mock.MagicMock(test_option="poodle_config_value")
        assert config.get_option_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        ) == ("poodle_config_value", "poodle_config.py")

    def test_get_config_data_value(self):
        assert config.get_option_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        ) == ("config_file_value", "config file")

    def test_not_found(self):
        value, source = config.get_option_from_config(
            option_name="test_option",
            config_data={},
            command_line="",
        )
        assert value is None
        assert source is None

    def test_command_line_false(self):
        value, source = config.get_option_from_config(
            option_name="test_option",
            config_data={},
            command_line=False,
        )
        assert value is False
        assert source == "Command Line"


class TestGetDictFromConfig:
    def test_default_only(self):
        assert config.get_dict_from_config(option_name="mutator_opts", config_data={}) == {}

    def test_config_data(self):
        assert config.get_dict_from_config(
            option_name="mutator_opts",
            default={
                "bin_op_level": "max",
                "custom": {"output": "XYZ"},
            },
            config_data={
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                    "custom": {"custom_option": "EFGH"},
                },
                "runner_opts": {
                    "mutator_file_option": "QWERTY",
                },
            },
        ) == {
            "bin_op_level": "min",
            "config_file_option": "ABCD",
            "custom": {"custom_option": "EFGH", "output": "XYZ"},
        }

    def test_config_data_invalid(self):
        with pytest.raises(PoodleInputError, match="^mutator_opts in config file must be a valid dict$"):
            config.get_dict_from_config(
                option_name="mutator_opts",
                default={"bin_op_level": "std"},
                config_data={"mutator_opts": "min"},
            )

    def test_poodle_config(self):
        config.poodle_config = mock.MagicMock(
            mutator_opts={
                "bin_op_level": "max",
                "poodle_config_option": "EFGH",
                "custom": {"output": "XYZ"},
            },
        )
        assert config.get_dict_from_config(
            option_name="mutator_opts",
            default={"bin_op_level": "std"},
            config_data={
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                    "custom": {"custom_option": "EFGH"},
                },
            },
            command_line={"cmd_option": "cmd_value", "custom": {"custom_option": "UIO"}},
        ) == {
            "bin_op_level": "max",
            "config_file_option": "ABCD",
            "poodle_config_option": "EFGH",
            "cmd_option": "cmd_value",
            "custom": {"custom_option": "UIO", "output": "XYZ"},
        }

    def test_poodle_config_invalid(self):
        config.poodle_config = mock.MagicMock(mutator_opts="min")
        with pytest.raises(PoodleInputError, match="^poodle_config.mutator_opts must be a valid dict$"):
            config.get_dict_from_config(option_name="mutator_opts", default={"bin_op_level": "std"}, config_data={})
