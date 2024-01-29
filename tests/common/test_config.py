from __future__ import annotations

import importlib
import logging
from pathlib import Path
from unittest import mock

import pytest
from ordered_set import OrderedSet
from wcmatch import glob

from poodle.common import config
from poodle.common.exceptions import PoodleInputError


@pytest.fixture(autouse=True)
def _setup():
    importlib.reload(config)
    yield


class TestLogFormat:
    def test_log_format(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"log_format": "TEST"}
        assert config_data.log_format == "TEST"

    def test_log_format_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.log_format == "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"

    @mock.patch("poodle.common.config.PoodleConfigData.get_str_from_config")
    def test_log_format_cached(self, mock_get_str_from_config: mock.MagicMock):
        mock_get_str_from_config.return_value = "TEST"
        config_data = config.PoodleConfigData()
        assert config_data.log_format == "TEST"
        assert config_data.log_format == "TEST"
        assert mock_get_str_from_config.call_count == 1


class TestVerbosityLevel:
    def test_verbosity_level(self):
        config_data = config.PoodleConfigData({"verbose": 3, "quiet": 2})
        assert config_data.verbosity_level == 1

    def test_verbosity_level_verbose(self):
        config_data = config.PoodleConfigData({"verbose": 3})
        assert config_data.verbosity_level == 3

    def test_verbosity_level_quiet(self):
        config_data = config.PoodleConfigData({"quiet": 2})
        assert config_data.verbosity_level == -2

    def test_verbosity_level_default(self):
        config_data = config.PoodleConfigData()
        assert config_data.verbosity_level == 0

    def test_verbosity_level_cached(self):
        config_data = config.PoodleConfigData({"verbose": 3, "quiet": 2})
        assert config_data.verbosity_level == 1
        config_data.cmd_kwargs = {"verbose": 6, "quiet": 2}
        assert config_data.verbosity_level == 1


class TestGetCmdLineLogLevel:
    def test_get_cmd_line_log_level_3(self):
        config_data = config.PoodleConfigData({"verbose": 3})
        assert config_data._get_cmd_line_log_level() == logging.CRITICAL

    def test_get_cmd_line_log_level_2(self):
        config_data = config.PoodleConfigData({"verbose": 2})
        assert config_data._get_cmd_line_log_level() == logging.CRITICAL

    def test_get_cmd_line_log_level_1(self):
        config_data = config.PoodleConfigData({"verbose": 1})
        assert config_data._get_cmd_line_log_level() == logging.ERROR

    def test_get_cmd_line_log_level_0(self):
        config_data = config.PoodleConfigData()
        assert config_data._get_cmd_line_log_level() == logging.WARN

    def test_get_cmd_line_log_level_n1(self):
        config_data = config.PoodleConfigData({"quiet": 1})
        assert config_data._get_cmd_line_log_level() == logging.INFO

    def test_get_cmd_line_log_level_n2(self):
        config_data = config.PoodleConfigData({"quiet": 2})
        assert config_data._get_cmd_line_log_level() == logging.DEBUG


class TestLogLevel:
    def test_log_level(self):
        config_data = config.PoodleConfigData({"quiet": 2})
        config_data.config_file_data = {"log_level": "ERROR"}
        assert config_data.log_level == "ERROR"

    def test_log_level_default(self):
        config_data = config.PoodleConfigData({"quiet": 2})
        config_data.config_file_data = {}
        assert config_data.log_level == logging.DEBUG

    @mock.patch("poodle.common.config.PoodleConfigData.get_any_from_config")
    def test_log_level_cached(self, get_any_from_config: mock.MagicMock):
        get_any_from_config.return_value = "WARN"
        config_data = config.PoodleConfigData()
        assert config_data.log_level == "WARN"
        assert config_data.log_level == "WARN"
        assert get_any_from_config.call_count == 1


class TestProjectName:
    def test_project_name(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"project_name": "TEST"}
        assert config_data.project_name == "TEST"

    def test_project_name_pyproject(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        config_data._pyproject_toml = {"project": {"name": "TEST"}}
        assert config_data.project_name == "TEST"

    def test_project_name_pyproject_not_found(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        config_data._pyproject_toml = {}
        assert config_data.project_name == ""


class TestProjectVersion:
    def test_project_version(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"project_version": "TEST"}
        assert config_data.project_version == "TEST"

    def test_project_version_pyproject(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        config_data._pyproject_toml = {"project": {"version": "TEST"}}
        assert config_data.project_version == "TEST"

    def test_project_version_pyproject_not_found(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        config_data._pyproject_toml = {}
        assert config_data.project_version == ""


class TestSourceFolders:
    @mock.patch("poodle.common.config.PoodleConfigData.get_path_list_from_config")
    def test_source_folders(self, get_path_list_from_config: mock.MagicMock):
        mock_src = mock.MagicMock(spec=Path, is_dir=lambda: True)
        mock_lib = mock.MagicMock(spec=Path, is_dir=lambda: False)
        mock_source = mock.MagicMock(spec=Path, is_dir=lambda: True)
        get_path_list_from_config.return_value = [mock_source]

        config_data = config.PoodleConfigData()
        config_data.default_source_folders = [mock_src, mock_lib]
        assert config_data.source_folders == [mock_source]

        get_path_list_from_config.assert_called_once_with("source_folders", "sources")

    @mock.patch("poodle.common.config.PoodleConfigData.get_path_list_from_config")
    def test_source_folders_default(self, get_path_list_from_config: mock.MagicMock):
        mock_src = mock.MagicMock(spec=Path, is_dir=lambda: True)
        mock_lib = mock.MagicMock(spec=Path, is_dir=lambda: False)
        get_path_list_from_config.return_value = []

        config_data = config.PoodleConfigData()
        assert config_data.default_source_folders == [Path("src"), Path("lib")]
        config_data.default_source_folders = [mock_src, mock_lib]
        assert config_data.source_folders == [mock_src]

    @mock.patch("poodle.common.config.PoodleConfigData.get_path_list_from_config")
    def test_source_folders_not_found(self, get_path_list_from_config: mock.MagicMock):
        mock_src = mock.MagicMock(spec=Path, is_dir=lambda: False)
        mock_lib = mock.MagicMock(spec=Path, is_dir=lambda: False)
        get_path_list_from_config.return_value = []

        config_data = config.PoodleConfigData()
        config_data.default_source_folders = [mock_src, mock_lib]
        with pytest.raises(PoodleInputError, match="^No source folder found to mutate.$"):
            config_data.source_folders

    @mock.patch("poodle.common.config.PoodleConfigData.get_path_list_from_config")
    def test_source_folders_not_a_folder(self, get_path_list_from_config: mock.MagicMock):
        mock_src = mock.MagicMock(spec=Path, is_dir=lambda: False)
        mock_lib = mock.MagicMock(spec=Path, is_dir=lambda: False)
        mock_source = mock.MagicMock(spec=Path, is_dir=lambda: False, __repr__=lambda _: "source")
        get_path_list_from_config.return_value = [mock_source]

        config_data = config.PoodleConfigData()
        config_data.default_source_folders = [mock_src, mock_lib]
        with pytest.raises(PoodleInputError, match="Source 'source' must be a folder."):
            config_data.source_folders

    @mock.patch("poodle.common.config.PoodleConfigData.get_path_list_from_config")
    def test_source_folders_cached(self, get_path_list_from_config: mock.MagicMock):
        mock_src = mock.MagicMock(spec=Path, is_dir=lambda: True)
        mock_lib = mock.MagicMock(spec=Path, is_dir=lambda: False)
        mock_source = mock.MagicMock(spec=Path, is_dir=lambda: True)
        get_path_list_from_config.return_value = [mock_source]

        config_data = config.PoodleConfigData()
        config_data.default_source_folders = [mock_src, mock_lib]
        assert config_data.source_folders == [mock_source]
        assert config_data.source_folders == [mock_source]

        assert get_path_list_from_config.call_count == 1


class TestFileFlags:
    def test_file_flags(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"file_flags": 234}
        assert config_data.file_flags == 234

    def test_file_flags_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.file_flags == glob.GLOBSTAR | glob.NODIR

    @mock.patch("poodle.common.config.PoodleConfigData.get_int_from_config")
    def test_file_flags_cached(self, get_int_from_config: mock.MagicMock):
        get_int_from_config.return_value = 123
        config_data = config.PoodleConfigData()
        assert config_data.file_flags == 123
        assert config_data.file_flags == 123
        assert get_int_from_config.call_count == 1


class TestOnlyFiles:
    def test_only_files(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"only_files": ["test"]}
        assert config_data.only_files == ["test"]

    def test_only_files_cmd(self):
        config_data = config.PoodleConfigData({"only": ["test"]})
        config_data.config_file_data = {}
        assert config_data.only_files == ["test"]

    def test_only_files_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.only_files == []

    @mock.patch("poodle.common.config.PoodleConfigData.get_str_list_from_config")
    def test_only_files_cached(self, get_str_list_from_config: mock.MagicMock):
        get_str_list_from_config.return_value = ["test"]
        config_data = config.PoodleConfigData()
        assert config_data.only_files == ["test"]
        assert config_data.only_files == ["test"]
        assert get_str_list_from_config.call_count == 1


class TestFileFilters:
    def test_file_filters(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"file_filters": ["test"]}
        assert config_data.file_filters == ["test"]

    def test_file_filters_exclude(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"file_filters": ["test"], "exclude": ["test2"]}
        assert config_data.file_filters == ["test", "test2"]

    def test_file_filters_cmd(self):
        config_data = config.PoodleConfigData({"exclude": ["test3"]})
        config_data.config_file_data = {"file_filters": ["test"], "exclude": ["test2"]}
        assert config_data.file_filters == ["test", "test2", "test3"]

    def test_file_filters_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.file_filters == ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]

    @mock.patch("poodle.common.config.PoodleConfigData.get_str_list_from_config")
    def test_file_filters_cached(self, get_str_list_from_config: mock.MagicMock):
        get_str_list_from_config.side_effect = [["test"], ["test2"]]
        config_data = config.PoodleConfigData()
        assert config_data.file_filters == ["test", "test2"]
        assert config_data.file_filters == ["test", "test2"]
        assert get_str_list_from_config.call_count == 2


class TestFileCopyFlags:
    def test_file_copy_flags(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"file_copy_flags": 234}
        assert config_data.file_copy_flags == 234

    def test_file_copy_flags_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.file_copy_flags == glob.GLOBSTAR | glob.NODIR

    @mock.patch("poodle.common.config.PoodleConfigData.get_int_from_config")
    def test_file_copy_flags_cached(self, get_int_from_config: mock.MagicMock):
        get_int_from_config.return_value = 123
        config_data = config.PoodleConfigData()
        assert config_data.file_copy_flags == 123
        assert config_data.file_copy_flags == 123
        assert get_int_from_config.call_count == 1


class TestFileCopyFilters:
    def test_file_copy_filters(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"file_copy_filters": ["test"]}
        assert config_data.file_copy_filters == ["test"]

    def test_file_copy_filters_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.file_copy_filters == ["__pycache__/**"]

    @mock.patch("poodle.common.config.PoodleConfigData.get_str_list_from_config")
    def test_file_copy_filters_cached(self, get_str_list_from_config: mock.MagicMock):
        get_str_list_from_config.return_value = ["test"]
        config_data = config.PoodleConfigData()
        assert config_data.file_copy_filters == ["test"]
        assert config_data.file_copy_filters == ["test"]
        assert get_str_list_from_config.call_count == 1


class TestWorkFolder:
    def test_work_folder(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"work_folder": Path("test")}
        assert config_data.work_folder == Path("test")

    def test_work_folder_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.work_folder == Path(".poodle-temp")

    @mock.patch("poodle.common.config.PoodleConfigData.get_path_from_config")
    def test_work_folder_cached(self, get_path_from_config: mock.MagicMock):
        get_path_from_config.return_value = Path("test")
        config_data = config.PoodleConfigData()
        assert config_data.work_folder == Path("test")
        assert config_data.work_folder == Path("test")
        assert get_path_from_config.call_count == 1


class TestDefaultMaxWorkers:
    @mock.patch("poodle.common.config.os")
    def test_default_max_workers_getaffinity(self, mock_os: mock.MagicMock):
        mock_os.sched_getaffinity.return_value = [1, 2, 3]
        mock_os.cpu_count.return_value = 4
        config_data = config.PoodleConfigData()
        assert config_data.default_max_workers() == 2
        mock_os.sched_getaffinity.assert_called_once_with(0)

    @pytest.mark.parametrize(
        ("cpu_count", "expected"),
        [
            (1, 1),
            (2, 1),
            (3, 2),
            (0, 1),
            (None, 1),
        ],
    )
    @mock.patch("poodle.common.config.os")
    def test_default_max_workers_cpu_count(self, mock_os: mock.MagicMock, cpu_count, expected):
        del mock_os.sched_getaffinity
        mock_os.cpu_count.return_value = cpu_count
        config_data = config.PoodleConfigData()
        assert config_data.default_max_workers() == expected


class TestMaxWorkers:
    @mock.patch("poodle.common.config.PoodleConfigData.default_max_workers")
    def test_max_workers(self, default_max_workers: mock.MagicMock):
        default_max_workers.return_value = 3
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"max_workers": 4}
        assert config_data.max_workers == 4

    @mock.patch("poodle.common.config.PoodleConfigData.default_max_workers")
    def test_max_workers_cmd(self, default_max_workers: mock.MagicMock):
        default_max_workers.return_value = 3
        config_data = config.PoodleConfigData({"workers": 5})
        config_data.config_file_data = {}
        assert config_data.max_workers == 5

    @mock.patch("poodle.common.config.PoodleConfigData.default_max_workers")
    def test_max_workers_default(self, default_max_workers: mock.MagicMock):
        default_max_workers.return_value = 3
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.max_workers == 3

    @mock.patch("poodle.common.config.PoodleConfigData.default_max_workers")
    def test_max_workers_cached(self, default_max_workers: mock.MagicMock):
        default_max_workers.return_value = 3
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.max_workers == 3
        assert config_data.max_workers == 3
        assert default_max_workers.call_count == 1


class TestSkipDeleteFolder:
    def test_max_workers(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"skip_delete_folder": True}
        assert config_data.skip_delete_folder is True

    def test_max_workers_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.skip_delete_folder is False

    @mock.patch("poodle.common.config.PoodleConfigData.get_bool_from_config")
    def test_max_workers_cached(self, get_bool_from_config: mock.MagicMock):
        get_bool_from_config.return_value = True
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.skip_delete_folder is True
        assert config_data.skip_delete_folder is True
        assert get_bool_from_config.call_count == 1


class TestGetCmdLineEchoEnabled:
    def test_get_cmd_line_echo_enabled_v(self):
        config_data = config.PoodleConfigData({"verbose": 1})
        assert config_data._get_cmd_line_echo_enabled() is True

    def test_get_cmd_line_echo_enabled_q(self):
        config_data = config.PoodleConfigData({"quiet": 1})
        assert config_data._get_cmd_line_echo_enabled() is False

    def test_get_cmd_line_echo_enabled(self):
        config_data = config.PoodleConfigData()
        assert config_data._get_cmd_line_echo_enabled() is None


class TestEchoEnabled:
    def test_echo_enabled(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.echo_enabled is True

    def test_echo_enabled_cmd(self):
        config_data = config.PoodleConfigData({"quiet": 1})
        config_data.config_file_data = {}
        assert config_data.echo_enabled is False

    def test_echo_enabled_cfg(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"echo_enabled": False}
        assert config_data.echo_enabled is False

    @mock.patch("poodle.common.config.PoodleConfigData.get_bool_from_config")
    def test_echo_enabled_cached(self, get_bool_from_config: mock.MagicMock):
        get_bool_from_config.return_value = True
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.echo_enabled is True
        assert config_data.echo_enabled is True
        assert get_bool_from_config.call_count == 1


class TestEchoNoColor:
    def test_echo_no_color_true(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"echo_no_color": True}
        assert config_data.echo_no_color is True

    def test_echo_no_color_false(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"echo_no_color": False}
        assert config_data.echo_no_color is False

    def test_echo_no_color_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.echo_no_color is False

    @mock.patch("poodle.common.config.PoodleConfigData.get_bool_from_config")
    def test_echo_no_color_cached(self, get_bool_from_config: mock.MagicMock):
        get_bool_from_config.return_value = True
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.echo_no_color is True
        assert config_data.echo_no_color is True
        assert get_bool_from_config.call_count == 1


class TestMutatorFilterPatterns:
    def test_mutator_filter_patterns(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"mutator_filter_patterns": ["test"]}
        assert config_data.mutator_filter_patterns == [r'.*__name__\s*==\s*(\'|")__main__(\'|").*', "test"]

    def test_mutator_filter_patterns_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.mutator_filter_patterns == [r'.*__name__\s*==\s*(\'|")__main__(\'|").*']

    def test_mutator_filter_patterns_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_str_list_from_config = mock.MagicMock(return_value=[])
        assert config_data.mutator_filter_patterns == config_data.default_mutator_filter_patterns
        assert config_data.mutator_filter_patterns == config_data.default_mutator_filter_patterns
        assert config_data.get_str_list_from_config.call_count == 1


class TestSkipMutators:
    def test_skip_mutators(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"skip_mutators": ["Test"]}
        assert config_data.skip_mutators == ["test"]

    def test_skip_mutators_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.skip_mutators == []

    def test_skip_mutators_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_str_list_from_config = mock.MagicMock(return_value=[])
        assert config_data.skip_mutators == []
        assert config_data.skip_mutators == []
        assert config_data.get_str_list_from_config.call_count == 1


class TestOnlyMutators:
    def test_only_mutators(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"only_mutators": ["Test"]}
        assert config_data.only_mutators == ["test"]

    def test_only_mutators_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.only_mutators == []

    def test_only_mutators_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_str_list_from_config = mock.MagicMock(return_value=[])
        assert config_data.only_mutators == []
        assert config_data.only_mutators == []
        assert config_data.get_str_list_from_config.call_count == 1


class TestMinTimeout:
    def test_min_timeout(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"min_timeout": 123}
        assert config_data.min_timeout == 123

    def test_min_timeout_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.min_timeout == 10

    def test_min_timeout_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_int_from_config = mock.MagicMock(return_value=123)
        assert config_data.min_timeout == 123
        assert config_data.min_timeout == 123
        assert config_data.get_int_from_config.call_count == 1


class TestTimeoutMultiplier:
    def test_timeout_multiplier(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"timeout_multiplier": 123}
        assert config_data.timeout_multiplier == 123

    def test_timeout_multiplier_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.timeout_multiplier == 10

    def test_timeout_multiplier_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_int_from_config = mock.MagicMock(return_value=123)
        assert config_data.timeout_multiplier == 123
        assert config_data.timeout_multiplier == 123
        assert config_data.get_int_from_config.call_count == 1


class TestRunner:
    def test_runner(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"runner": "test"}
        assert config_data.runner == "test"

    def test_runner_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.runner == "command_line"

    def test_runner_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_str_from_config = mock.MagicMock(return_value="test")
        assert config_data.runner == "test"
        assert config_data.runner == "test"
        assert config_data.get_str_from_config.call_count == 1


class TestReporters:
    def test_reporters(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {"reporters": ["test"]}
        assert config_data.reporters == OrderedSet(["test"])

    def test_reporters_cmd(self):
        config_data = config.PoodleConfigData({"report": ["test"]})
        config_data.config_file_data = {}
        assert config_data.reporters == OrderedSet(["test"])

    def test_reporters_default(self):
        config_data = config.PoodleConfigData()
        config_data.config_file_data = {}
        assert config_data.reporters == OrderedSet(["sysout"])

    def test_reporters_cached(self):
        config_data = config.PoodleConfigData()
        config_data.get_str_list_from_config = mock.MagicMock(return_value=[])
        assert config_data.reporters == OrderedSet(["sysout"])
        assert config_data.reporters == OrderedSet(["sysout"])
        assert config_data.get_str_list_from_config.call_count == 1
