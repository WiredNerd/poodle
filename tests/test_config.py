import importlib
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest

from poodle import PoodleInvalidInput, config


@pytest.fixture(autouse=True)
def _test_wrapper():
    importlib.reload(config)
    config.poodle_config = None
    config.default_mutator_opts = {"bin_op_level": "std"}
    config.default_runner_opts = {"command_line": "pytest tests"}
    yield
    importlib.reload(config)


#TODO build_config

class TestConfigFile:
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

        mock_path.side_effect = get_path

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_cmd_line(self, mock_path):
        self.setup_mock_path(mock_path, True, True, True)
        assert config.get_config_file_path("config.toml") == mock_path.config_file_path

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_cmd_line_not_found(self, mock_path):
        self.setup_mock_path(mock_path, False, True, True)
        with pytest.raises(PoodleInvalidInput, match="^Config file not found: --config_file='config.toml'$"):
            config.get_config_file_path("config.toml")

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_poodle(self, mock_path):
        self.setup_mock_path(mock_path, False, True, True)
        assert config.get_config_file_path(None) == mock_path.poodle_toml_path

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_pyproject(self, mock_path):
        self.setup_mock_path(mock_path, False, False, True)
        assert config.get_config_file_path(None) == mock_path.pyproject_toml_path

    @mock.patch("poodle.config.Path")
    def test_get_config_file_path_none(self, mock_path):
        self.setup_mock_path(mock_path, False, False, False)
        assert config.get_config_file_path(None) is None

    def test_get_config_file_data_no_file(self):
        assert config.get_config_file_data(None) == {}

    @mock.patch("poodle.config.get_config_file_toml")
    def test_get_config_file_data_toml(self, get_config_file_toml):
        get_config_file_toml.return_value = {"test": "value"}
        assert config.get_config_file_data(Path("config.toml")) == {"test": "value"}
        get_config_file_toml.assert_called_with(Path("config.toml"))

    def test_get_config_file_data_invalid(self):
        with pytest.raises(PoodleInvalidInput, match="^Config file type not supported: --config_file='config.txt'$"):
            config.get_config_file_data(Path("config.txt"))


config_toml_poodle = """
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


class TestGetConfigFile:
    def test_get_config_file_toml_poodle(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_poodle, encoding="utf-8"))
        assert config.get_config_file_toml(file_path) == {"test": "value1"}
        file_path.open.assert_called_with(mode="rb")

    def test_get_config_file_toml_tool_poodle(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_tool_poodle, encoding="utf-8"))
        assert config.get_config_file_toml(file_path) == {"test": "value2"}
        file_path.open.assert_called_with(mode="rb")

    def test_get_config_file_toml_no_data(self):
        file_path = mock.MagicMock()
        file_path.open.return_value = BytesIO(bytes(config_toml_no_data, encoding="utf-8"))
        assert config.get_config_file_toml(file_path) == {}
        file_path.open.assert_called_with(mode="rb")


class TestGetSourceFolders:
    def test_get_source_folders(self):
        path_src = mock.MagicMock()
        path_src.is_dir.return_value = True

        source = mock.MagicMock()
        config_file = mock.MagicMock()

        with mock.patch("poodle.config.get_source_folders_from_config") as get_source_folders_from_config:
            get_source_folders_from_config.return_value = [path_src]
            assert config.get_source_folders(source, config_file) == [path_src]
            get_source_folders_from_config.assert_called_with(source, config_file)

    def test_get_source_folders_not_found(self):
        with mock.patch("poodle.config.get_source_folders_from_config") as get_source_folders_from_config:
            get_source_folders_from_config.return_value = []
            with pytest.raises(PoodleInvalidInput, match="^No source folder found to mutate.$"):
                config.get_source_folders(tuple(), {})

    def test_get_source_folders_not_folder(self):
        path_src = mock.MagicMock()
        path_src.is_dir.return_value = False
        path_lib = mock.MagicMock()
        path_lib.is_dir.return_value = True

        with mock.patch("poodle.config.get_source_folders_from_config") as get_source_folders_from_config:
            get_source_folders_from_config.return_value = [path_lib, path_src]
            with pytest.raises(PoodleInvalidInput, match="Source must be a folder.") as err:
                config.get_source_folders(tuple(), {})
            assert err.value.args == ("Source must be a folder.", str(path_src))

    def test_get_source_folders_from_config_sources(self):
        assert config.get_source_folders_from_config(("src1", "src2"), {}) == [Path("src1"), Path("src2")]

    def test_get_source_folders_from_config_poodle_config(self):
        config.poodle_config = mock.MagicMock(source_folders=["lib1", "lib2"])
        assert config.get_source_folders_from_config(tuple(), {}) == [Path("lib1"), Path("lib2")]

    def test_get_source_folders_from_config_poodle_config_invalid_iter(self):
        config.poodle_config = mock.MagicMock(source_folders=34)
        with pytest.raises(
            PoodleInvalidInput,
            match=r"^poodle_config.source_folders must be of type Iterable\[PathStr\]$",
        ):
            config.get_source_folders_from_config(tuple(), {})

    def test_get_source_folders_from_config_poodle_config_invalid_str(self):
        config.poodle_config = mock.MagicMock(source_folders=[34])
        with pytest.raises(
            PoodleInvalidInput,
            match=r"^poodle_config.source_folders must be of type Iterable\[PathStr\]$",
        ):
            config.get_source_folders_from_config(tuple(), {})

    def test_get_source_folders_from_config_poodle_config_file(self):
        assert config.get_source_folders_from_config(
            tuple(),
            {"source_folders": ["src1", "src2"]},
        ) == [Path("src1"), Path("src2")]

    def test_get_source_folders_from_config_poodle_config_file_invalid_iter(self):
        with pytest.raises(
            PoodleInvalidInput,
            match=r"^source_folders in config file must be of type Iterable\[str\]$",
        ):
            config.get_source_folders_from_config(tuple(), {"source_folders": 55})

    def test_get_source_folders_from_config_poodle_config_file_invalid_str(self):
        with pytest.raises(
            PoodleInvalidInput,
            match=r"^source_folders in config file must be of type Iterable\[str\]$",
        ):
            config.get_source_folders_from_config(tuple(), {"source_folders": [55]})

    def test_get_source_folders_from_config_default(self):
        config.poodle_config = mock.MagicMock(source_folders=[])

        path_src = mock.MagicMock()
        path_src.is_dir.return_value = False
        path_lib = mock.MagicMock()
        path_lib.is_dir.return_value = True
        config.default_source_folders = [path_src, path_lib]

        assert config.get_source_folders_from_config(tuple(), {}) == [path_lib]


class TestGetMutatorOpts:
    def test_default_only(self):
        assert config.get_mutator_opts_from_config({}) == {
            "bin_op_level": "std",
        }

    def test_config_file(self):
        assert config.get_mutator_opts_from_config(
            {
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                },
                "runner_opts": {
                    "mutator_file_option": "QWERTY",
                },
            }
        ) == {
            "bin_op_level": "min",
            "config_file_option": "ABCD",
        }

    def test_config_file_invalid(self):
        with pytest.raises(PoodleInvalidInput, match="^mutator_opts in config file must be a valid dict$"):
            config.get_mutator_opts_from_config({"mutator_opts": "min"})

    def test_poodle_config(self):
        config.poodle_config = mock.MagicMock(
            mutator_opts={
                "bin_op_level": "max",
                "poodle_config_option": "EFGH",
            }
        )
        assert config.get_mutator_opts_from_config(
            {
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                },
            }
        ) == {
            "bin_op_level": "max",
            "config_file_option": "ABCD",
            "poodle_config_option": "EFGH",
        }

    def test_poodle_config_invalid(self):
        config.poodle_config = mock.MagicMock(mutator_opts="min")
        with pytest.raises(PoodleInvalidInput, match="^poodle_config.mutator_opts must be a valid dict$"):
            config.get_mutator_opts_from_config({})


class TestGetRunnerOpts:
    def test_default_only(self):
        assert config.get_runner_opts_from_config({}) == {
            "command_line": "pytest tests",
        }

    def test_config_file(self):
        assert config.get_runner_opts_from_config(
            {
                "runner_opts": {
                    "command_line": "pytest test2",
                    "config_file_option": "ABCD",
                },
                "mutator_opts": {
                    "mutator_file_option": "QWERTY",
                },
            }
        ) == {
            "command_line": "pytest test2",
            "config_file_option": "ABCD",
        }

    def test_config_file_invalid(self):
        with pytest.raises(PoodleInvalidInput, match="^runner_opts in config file must be a valid dict$"):
            config.get_runner_opts_from_config({"runner_opts": "pytest test2"})

    def test_poodle_config(self):
        config.poodle_config = mock.MagicMock(
            runner_opts={
                "command_line": "pytest test3",
                "poodle_config_option": "EFGH",
            }
        )
        assert config.get_runner_opts_from_config(
            {
                "runner_opts": {
                    "command_line": "pytest test2",
                    "config_file_option": "ABCD",
                },
            }
        ) == {
            "command_line": "pytest test3",
            "config_file_option": "ABCD",
            "poodle_config_option": "EFGH",
        }

    def test_poodle_config_invalid(self):
        config.poodle_config = mock.MagicMock(runner_opts="pytest test3")
        with pytest.raises(PoodleInvalidInput, match="^poodle_config.runner_opts must be a valid dict$"):
            config.get_runner_opts_from_config({})
