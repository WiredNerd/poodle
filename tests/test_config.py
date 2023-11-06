import importlib
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest

from poodle import PoodleInputError, config


@pytest.fixture(autouse=True)
def _test_wrapper():
    importlib.reload(config)
    config.poodle_config = None
    config.default_mutator_opts = {"bin_op_level": "std"}
    config.default_runner_opts = {"command_line": "pytest tests"}
    yield
    importlib.reload(config)


@pytest.fixture()
def get_any_from_config():
    with mock.patch("poodle.config.get_any_from_config") as get_any_from_config:
        yield get_any_from_config


def test_defaults():
    importlib.reload(config)
    assert config.default_source_folders == [Path("src"), Path("lib")]
    assert config.default_file_filters == [r"^test_", r"_test$"]
    assert config.default_work_folder == Path(".poodle-temp")
    assert config.default_mutator_opts == {}
    assert config.default_runner_opts == {
        "command_line": "pytest -x --assert=plain --no-header --no-summary -o pythonpath="
    }


class TestBuildConfig:
    @mock.patch("poodle.config.get_config_file_path")
    @mock.patch("poodle.config.get_config_file_data")
    @mock.patch("poodle.config.get_source_folders")
    @mock.patch("poodle.config.get_str_list_from_config")
    @mock.patch("poodle.config.get_path_from_config")
    @mock.patch("poodle.config.get_dict_from_config")
    def test_build_config(
        self,
        get_dict_from_config,
        get_path_from_config,
        get_str_list_from_config,
        get_source_folders,
        get_config_file_data,
        get_config_file_path,
    ):
        get_dict_from_config.side_effect = [{"mutator": "value"}, {"runner": "value"}]

        command_line_sources = (Path("src"),)
        config_file = Path("config.toml")

        config_file_path = get_config_file_path.return_value
        config_file_data = get_config_file_data.return_value

        assert config.build_config(command_line_sources, config_file) == config.PoodleConfig(
            config_file=config_file_path,
            source_folders=get_source_folders.return_value,
            file_filters=get_str_list_from_config.return_value,
            work_folder=get_path_from_config.return_value,
            mutator_opts={"mutator": "value"},
            runner_opts={"runner": "value"},
        )

        get_source_folders.assert_called_with(command_line_sources, config_file_data)
        get_str_list_from_config.assert_called_with(
            "file_filters", config_file_data, default=config.default_file_filters
        )
        get_path_from_config.assert_called_with("work_folder", config_file_data, default=config.default_work_folder)
        get_dict_from_config.assert_any_call("mutator_opts", config_file_data, default=config.default_mutator_opts)
        get_dict_from_config.assert_any_call("runner_opts", config_file_data, default=config.default_runner_opts)
        assert get_dict_from_config.call_count == 2


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
        with pytest.raises(PoodleInputError, match="^Config file not found: --config_file='config.toml'$"):
            config.get_config_file_path(path_config)

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
            config.get_source_folders(tuple(), {})

    @mock.patch("poodle.config.get_path_list_from_config")
    def test_get_source_folders_not_folder(self, get_path_list_from_config):
        path_project = mock.MagicMock()
        path_project.is_dir.return_value = False
        path_project.__repr__ = lambda _: "project"

        get_path_list_from_config.return_value = [path_project]

        with pytest.raises(PoodleInputError, match="Source 'project' must be a folder."):
            config.get_source_folders(tuple(), {})


class TestGetPathFromConfig:
    def test_default(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)

        config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=Path("command_line_value"),
            default=Path("default_value"),
        ) == Path("default_value")

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=Path("command_line_value"),
        )

    def test_default_inputs(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)

        config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
        ) == None

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": Path("config_file_value")},
            command_line=None,
        )

    def test_string(self, get_any_from_config):
        get_any_from_config.return_value = ("return_value", "Source Name")

        config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == Path("return_value")

    def test_empty_string(self, get_any_from_config):
        get_any_from_config.return_value = ("", "Source Name")

        config.get_path_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == Path("")

    def test_not_path(self, get_any_from_config):
        get_any_from_config.return_value = (123, "Source Name")

        with pytest.raises(PoodleInputError, match=r"^test_option from Source Name must be a valid StrPath$"):
            config.get_path_from_config(
                option_name="test_option", config_data={}, command_line=[], default=Path("default_value")
            )


class TestGetPathListFromConfig:
    def test_default(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)
        assert config.get_path_list_from_config(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=[Path("command_line_value")],
            default=[Path("default_value")],
        ) == [Path("default_value")]

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=[Path("command_line_value")],
        )

    def test_default_inputs(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)
        assert (
            config.get_path_list_from_config(
                option_name="test_option",
                config_data={"test_option": [Path("config_file_value")]},
            )
            == []
        )

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": [Path("config_file_value")]},
            command_line=tuple(),
        )

    def test_path(self, get_any_from_config):
        get_any_from_config.return_value = (Path("return_value"), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
        ) == [Path("return_value")]

    def test_string(self, get_any_from_config):
        get_any_from_config.return_value = ("return_value", "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
        ) == [Path("return_value")]

    def test_path_list(self, get_any_from_config):
        get_any_from_config.return_value = ((Path("return_value"), Path("other_value")), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
        ) == [Path("return_value"), Path("other_value")]

    def test_string_list(self, get_any_from_config):
        get_any_from_config.return_value = (("return_value", "other_value"), "Source Name")
        assert config.get_path_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
        ) == [Path("return_value"), Path("other_value")]

    def test_not_iterable(self, get_any_from_config):
        get_any_from_config.return_value = (123, "Source Name")
        with pytest.raises(
            PoodleInputError, match=r"^test_option from Source Name must be a valid Iterable\[StrPath\]$"
        ):
            config.get_path_list_from_config(
                option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
            )

    def test_not_path(self, get_any_from_config):
        get_any_from_config.return_value = ([123], "Source Name")
        with pytest.raises(
            PoodleInputError, match=r"^test_option from Source Name must be a valid Iterable\[StrPath\]$"
        ):
            config.get_path_list_from_config(
                option_name="test_option", config_data={}, command_line=[], default=[Path("default_value")]
            )


class TestGetStrFromConfig:
    def test_default(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)

        config.get_str_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == "default_value"

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
        )

    def test_default_inputs(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)

        config.get_str_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
        ) == ""

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        )

    def test_string(self, get_any_from_config):
        get_any_from_config.return_value = ("return_value", "Source Name")

        config.get_str_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == "return_value"

    def test_empty_string(self, get_any_from_config):
        get_any_from_config.return_value = ("", "Source Name")

        config.get_str_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == ""

    def test_convert(self, get_any_from_config):
        get_any_from_config.return_value = (Path("source.py"), "Source Name")

        config.get_str_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
            default="default_value",
        ) == "source.py"


class TestGetStrListFromConfig:
    def test_default(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)
        assert config.get_str_list_from_config(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
            default=["default_value"],
        ) == ["default_value"]

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=["command_line_value"],
        )

    def test_default_inputs(self, get_any_from_config):
        get_any_from_config.return_value = (None, None)
        assert (
            config.get_str_list_from_config(
                option_name="test_option",
                config_data={"test_option": ["config_file_value"]},
            )
            == []
        )

        get_any_from_config.assert_called_with(
            option_name="test_option",
            config_data={"test_option": ["config_file_value"]},
            command_line=tuple(),
        )

    def test_string(self, get_any_from_config):
        get_any_from_config.return_value = ("return_value", "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=["default_value"]
        ) == ["return_value"]

    def test_string_list(self, get_any_from_config):
        get_any_from_config.return_value = (("return_value", "other_value"), "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=["default_value"]
        ) == ["return_value", "other_value"]

    def test_string_list_convert(self, get_any_from_config):
        get_any_from_config.return_value = ((Path("output.txt"),), "Source Name")
        assert config.get_str_list_from_config(
            option_name="test_option", config_data={}, command_line=[], default=["default_value"]
        ) == ["output.txt"]

    def test_type_error(self, get_any_from_config):
        get_any_from_config.return_value = (123, "Source Name")
        with pytest.raises(PoodleInputError, match=r"^test_option from Source Name must be a valid Iterable\[str\]$"):
            config.get_str_list_from_config(
                option_name="test_option", config_data={}, command_line=[], default=["default_value"]
            )


class TestGetAnyFromConfig:
    def test_get_command_line_value(self):
        assert config.get_any_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="command_line_value",
        ) == ("command_line_value", "Command Line")

    def test_get_poodle_config_value(self):
        config.poodle_config = mock.MagicMock(test_option="poodle_config_value")
        assert config.get_any_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        ) == ("poodle_config_value", "poodle_config.py")

    def test_get_config_data_value(self):
        assert config.get_any_from_config(
            option_name="test_option",
            config_data={"test_option": "config_file_value"},
            command_line="",
        ) == ("config_file_value", "config file")

    def test_not_found(self):
        value, source = config.get_any_from_config(
            option_name="test_option",
            config_data={},
            command_line="",
        )
        assert value is None
        assert source is None


class TestGetDictFromConfig:
    def test_default_only(self):
        assert config.get_dict_from_config(
            option_name="mutator_opts",
            default={"bin_op_level": "std"},
            config_data={},
        ) == {
            "bin_op_level": "std",
        }

    def test_config_data(self):
        assert config.get_dict_from_config(
            option_name="mutator_opts",
            default={"bin_op_level": "std"},
            config_data={
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                },
                "runner_opts": {
                    "mutator_file_option": "QWERTY",
                },
            },
        ) == {
            "bin_op_level": "min",
            "config_file_option": "ABCD",
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
            }
        )
        assert config.get_dict_from_config(
            option_name="mutator_opts",
            default={"bin_op_level": "std"},
            config_data={
                "mutator_opts": {
                    "bin_op_level": "min",
                    "config_file_option": "ABCD",
                },
            },
        ) == {
            "bin_op_level": "max",
            "config_file_option": "ABCD",
            "poodle_config_option": "EFGH",
        }

    def test_poodle_config_invalid(self):
        config.poodle_config = mock.MagicMock(mutator_opts="min")
        with pytest.raises(PoodleInputError, match="^poodle_config.mutator_opts must be a valid dict$"):
            config.get_dict_from_config(option_name="mutator_opts", default={"bin_op_level": "std"}, config_data={})
