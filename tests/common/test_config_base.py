from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from mergedeep import merge

from poodle.common import config_base
from poodle.common.exceptions import PoodleInputError


@pytest.fixture()
def poodle_config():
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def get_poodle_config(poodle_config):
    with mock.patch("poodle.common.config_base.get_poodle_config") as get_poodle_config:
        get_poodle_config.return_value = poodle_config
        yield get_poodle_config


def build_path_tester(is_file: dict[str, bool] = {}) -> Any:
    class PathTester(Path):
        def is_file(self):
            return is_file.get(self.name, False)

    return PathTester


class TestPoodleConfigBase:
    def test_init(self, poodle_config):
        cmd_kwargs = {"cmd": "test"}
        config = config_base.PoodleConfigBase(cmd_kwargs)
        assert config.cmd_kwargs == cmd_kwargs
        assert config.poodle_config == poodle_config

    def test_init_default(self, poodle_config):
        config = config_base.PoodleConfigBase()
        assert config.cmd_kwargs == {}
        assert config.poodle_config == poodle_config


class TestConfigFile:
    def test_config_file_cmd(self, poodle_config):
        path_tester = build_path_tester(
            {
                "cmd_config_file.toml": True,
                "pc_config_file.toml": True,
                "poodle.toml": True,
                "pyproject.toml": True,
            }
        )

        cmd_config_file = path_tester("cmd_config_file.toml")
        cmd_kwargs = {"config_file": cmd_config_file}

        poodle_config.config_file = "pc_config_file.toml"

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase(cmd_kwargs)
            assert config.config_file == cmd_config_file

    def test_config_file_cmd_not_found(self, poodle_config):
        path_tester = build_path_tester(
            {
                "cmd_config_file.toml": False,
                "pc_config_file.toml": True,
                "poodle.toml": True,
                "pyproject.toml": True,
            }
        )

        cmd_config_file = path_tester("cmd_config_file.toml")
        cmd_kwargs = {"config_file": cmd_config_file}

        poodle_config.config_file = "pc_config_file.toml"

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase(cmd_kwargs)
            with pytest.raises(
                PoodleInputError,
                match=r"^Config file not found: 'cmd_config_file.toml'$",
            ):
                config.config_file

    def test_config_file_pc(self, poodle_config):
        path_tester = build_path_tester(
            {
                "pc_config_file.toml": True,
                "poodle.toml": True,
                "pyproject.toml": True,
            }
        )

        poodle_config.config_file = "pc_config_file.toml"

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase()
            assert config.config_file == path_tester("pc_config_file.toml")

    def test_config_file_pc_not_found(self, poodle_config):
        path_tester = build_path_tester(
            {
                "pc_config_file.toml": False,
                "poodle.toml": True,
                "pyproject.toml": True,
            }
        )

        poodle_config.config_file = "pc_config_file.toml"

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase()
            with pytest.raises(
                PoodleInputError,
                match=r"^poodle_config.config_file not found: 'pc_config_file.toml'$",
            ):
                config.config_file

    def test_config_file_poodle_toml(self, poodle_config):
        path_tester = build_path_tester(
            {
                "poodle.toml": True,
                "pyproject.toml": True,
            }
        )

        del poodle_config.config_file

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase()
            assert config.config_file == path_tester("poodle.toml")

    def test_config_file_pyproject_toml(self, poodle_config):
        path_tester = build_path_tester(
            {
                "poodle.toml": False,
                "pyproject.toml": True,
            }
        )

        del poodle_config.config_file

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase()
            assert config.config_file == path_tester("pyproject.toml")

    def test_config_file_none(self, poodle_config):
        path_tester = build_path_tester(
            {
                "poodle.toml": False,
                "pyproject.toml": False,
            }
        )

        del poodle_config.config_file

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase()
            assert config.config_file is None

    def test_config_file_cached(self):
        path_tester = build_path_tester({"cmd_config_file.toml": True})
        cmd_config_file = path_tester("cmd_config_file.toml")
        cmd_kwargs = {"config_file": cmd_config_file}

        with mock.patch("poodle.common.config_base.Path", path_tester):
            config = config_base.PoodleConfigBase(cmd_kwargs)
            assert config.config_file == cmd_config_file

        path_tester = build_path_tester({"cmd_config_file.toml": False})
        with mock.patch("poodle.common.config_base.Path", path_tester):
            assert config.config_file == cmd_config_file

        config.config_file = None
        assert config.config_file is None


class TestConfigFileData:
    def test_config_file_data(self):
        config = config_base.PoodleConfigBase()
        config.config_file = Path("test_config_base.toml")
        get_config_file_data_toml = mock.MagicMock()
        get_config_file_data_toml.return_value = {"test": "value"}
        config._get_config_file_data_toml = get_config_file_data_toml

        assert config.config_file_data == {"test": "value"}

    def test_config_file_data_no_file(self):
        config = config_base.PoodleConfigBase()
        config.config_file = None
        get_config_file_data_toml = mock.MagicMock()
        get_config_file_data_toml.return_value = {"test": "value"}
        config._get_config_file_data_toml = get_config_file_data_toml

        assert config.config_file_data == {}

    def test_config_file_data_not_supported(self):
        config = config_base.PoodleConfigBase()
        config.config_file = Path("test_config_base.txt")
        get_config_file_data_toml = mock.MagicMock()
        get_config_file_data_toml.return_value = {"test": "value"}
        config._get_config_file_data_toml = get_config_file_data_toml

        with pytest.raises(
            PoodleInputError,
            match=r"^Config file type not supported: 'test_config_base.txt'$",
        ):
            config.config_file_data

    def test_config_file_data_cached(self):
        config = config_base.PoodleConfigBase()
        config.config_file = Path("test_config_base.toml")
        get_config_file_data_toml = mock.MagicMock()
        get_config_file_data_toml.return_value = {"test": "value"}
        config._get_config_file_data_toml = get_config_file_data_toml

        assert config.config_file_data == {"test": "value"}
        assert config.config_file_data == {"test": "value"}
        get_config_file_data_toml.assert_called_once()
        config.config_file_data = {}
        assert config.config_file_data == {}

    def test_get_config_file_data_toml_tool(self):
        config = config_base.PoodleConfigBase()
        config.config_file = mock.MagicMock(__repr__=lambda _: "test_config_base.toml")
        with mock.patch("poodle.common.config_base.tomllib") as tomllib:
            tomllib.load.return_value = {"tool": {"poodle": {"test": "value"}}}
            assert config._get_config_file_data_toml() == {"test": "value"}

        config.config_file.open.assert_called_once_with(mode="rb")
        tomllib.load.assert_called_once_with(config.config_file.open.return_value)

    def test_get_config_file_data_toml_poodle(self):
        config = config_base.PoodleConfigBase()
        config.config_file = mock.MagicMock(__repr__=lambda _: "test_config_base.toml")
        with mock.patch("poodle.common.config_base.tomllib") as tomllib:
            tomllib.load.return_value = {"poodle": {"test": "value"}}
            assert config._get_config_file_data_toml() == {"test": "value"}

        config.config_file.open.assert_called_once_with(mode="rb")
        tomllib.load.assert_called_once_with(config.config_file.open.return_value)

    def test_get_config_file_data_toml_no_section(self):
        config = config_base.PoodleConfigBase()
        config.config_file = mock.MagicMock(__repr__=lambda _: "test_config_base.toml")
        with mock.patch("poodle.common.config_base.tomllib") as tomllib:
            tomllib.load.return_value = {"tool": {"test": "value"}}
            assert config._get_config_file_data_toml() == {}

        config.config_file.open.assert_called_once_with(mode="rb")
        tomllib.load.assert_called_once_with(config.config_file.open.return_value)

    def test_get_config_file_data_toml_err(self):
        config = config_base.PoodleConfigBase()
        config.config_file = mock.MagicMock(__repr__=lambda _: "test_config_base.toml")
        with pytest.raises(PoodleInputError) as e:
            config._get_config_file_data_toml()
        assert e.value.args[0] == "Error decoding toml file: 'test_config_base.toml'"
        assert e.value.args[1] == "Invalid statement (at end of document)"


class TestPyprojectToml:
    def test_pyproject_toml(self):
        config = config_base.PoodleConfigBase()
        with mock.patch("poodle.common.config_base.Path") as mock_path:
            file = mock_path.return_value
            file.is_file.return_value = True
            with mock.patch("poodle.common.config_base.tomllib") as tomllib:
                tomllib.load.return_value = {"test": "value"}
                assert config._pyproject_toml == {"test": "value"}
        mock_path.assert_called_once_with("pyproject.toml")
        file = mock_path.return_value
        file.is_file.assert_called_once_with()
        file.open.assert_called_once_with(mode="rb")
        tomllib.load.assert_called_once_with(file.open.return_value)

    def test_pyproject_toml_error(self):
        config = config_base.PoodleConfigBase()
        with mock.patch("poodle.common.config_base.Path") as mock_path:
            file = mock_path.return_value
            file.is_file.return_value = True
            assert config._pyproject_toml == {}
        mock_path.assert_called_once_with("pyproject.toml")
        file = mock_path.return_value
        file.is_file.assert_called_once_with()
        file.open.assert_called_once_with(mode="rb")

    def test_pyproject_toml_not_file(self):
        config = config_base.PoodleConfigBase()
        with mock.patch("poodle.common.config_base.Path") as mock_path:
            file = mock_path.return_value
            file.is_file.return_value = False
            with mock.patch("poodle.common.config_base.tomllib") as tomllib:
                assert config._pyproject_toml == {}
        mock_path.assert_called_once_with("pyproject.toml")
        file.is_file.assert_called_once_with()
        file.open.assert_not_called()
        tomllib.load.assert_not_called()

    def test_pyproject_toml_cached(self):
        config = config_base.PoodleConfigBase()
        with mock.patch("poodle.common.config_base.Path") as mock_path:
            file = mock_path.return_value
            file.is_file.return_value = True
            with mock.patch("poodle.common.config_base.tomllib") as tomllib:
                tomllib.load.return_value = {"test": "value"}
                assert config._pyproject_toml == {"test": "value"}
                assert config._pyproject_toml == {"test": "value"}
                config._pyproject_toml = {}
                assert config._pyproject_toml == {}
        mock_path.assert_called_once_with("pyproject.toml")
        file = mock_path.return_value
        file.is_file.assert_called_once_with()
        file.open.assert_called_once_with(mode="rb")
        tomllib.load.assert_called_once_with(file.open.return_value)


class TestMergeDictFromConfig:
    def test_merge_dict_from_config(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"test_option": {"key2": "file_data", "key4": "file_data"}}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = {"key3": "pc_data", "key5": "pc_data"}
        default = {"key1": "default", "key2": "default", "key3": "default"}
        assert config.merge_dict_from_config("test_option", default) == {
            "key1": "default",
            "key2": "file_data",
            "key3": "pc_data",
            "key4": "file_data",
            "key5": "pc_data",
        }

    def test_merge_dict_from_config_no_pc(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"test_option": {"key2": "file_data", "key4": "file_data"}}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        del config.poodle_config.test_option
        default = {"key1": "default", "key2": "default", "key3": "default"}
        assert config.merge_dict_from_config("test_option", default) == {
            "key1": "default",
            "key2": "file_data",
            "key3": "default",
            "key4": "file_data",
        }

    def test_merge_dict_from_config_no_file(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"other_option": {"key2": "file_data", "key4": "file_data"}}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = {"key3": "pc_data", "key5": "pc_data"}
        default = {"key1": "default", "key2": "default", "key3": "default"}
        assert config.merge_dict_from_config("test_option", default) == {
            "key1": "default",
            "key2": "default",
            "key3": "pc_data",
            "key5": "pc_data",
        }

    def test_merge_dict_from_config_no_default(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"test_option": {"key2": "file_data", "key4": "file_data"}}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = {"key3": "pc_data", "key5": "pc_data"}
        assert config.merge_dict_from_config("test_option") == {
            "key2": "file_data",
            "key3": "pc_data",
            "key4": "file_data",
            "key5": "pc_data",
        }

    def test_merge_dict_from_config_pc_invalid(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"test_option": {"key2": "file_data", "key4": "file_data"}}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = "pc_data"
        with pytest.raises(PoodleInputError, match="^test_option in poodle_config.py must be a valid dict$"):
            config.merge_dict_from_config("test_option")

    def test_merge_dict_from_config_file_invalid(self):
        config = config_base.PoodleConfigBase()
        config.config_file_data = {"test_option": "file_data"}
        config.config_file = Path("test_config_base.toml")
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = {"key3": "pc_data", "key5": "pc_data"}
        with pytest.raises(
            PoodleInputError,
            match="^test_option in config file test_config_base.toml must be a valid dict$",
        ):
            config.merge_dict_from_config("test_option")


class TestGetOptionFromConfig:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("cmd_value", ("cmd_value", "Command Line")),
            (True, (True, "Command Line")),
            (False, (False, "Command Line")),
            (None, ("pc_data", "poodle_config.py")),
        ],
    )
    def test_get_option_from_config_cmd(self, value, expected):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": value}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = "pc_data"
        config.config_file_data = {"test_option": "file_data"}
        assert config.get_option_from_config("test_option", "option") == expected

    def test_get_option_from_config_no_cmd(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = "pc_data"
        config.config_file_data = {"test_option": "file_data"}
        assert config.get_option_from_config("test_option","option") == ("pc_data", "poodle_config.py")

    def test_get_option_from_config_pc(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = "pc_data"
        config.config_file_data = {"test_option": "file_data"}
        assert config.get_option_from_config("test_option") == ("pc_data", "poodle_config.py")

    def test_get_option_from_config_file(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        config.poodle_config = mock.MagicMock()
        del config.poodle_config.test_option
        config.config_file_data = {"test_option": "file_data"}
        assert config.get_option_from_config("test_option") == ("file_data", "config file")

    def test_get_option_from_config_none(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        config.poodle_config = mock.MagicMock()
        del config.poodle_config.not_found
        config.config_file_data = {"test_option": "file_data"}
        assert config.get_option_from_config("not_found") == (None, None)


class TestGetAnyFromConfig:
    def test_get_any_from_config(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        config.poodle_config.test_option = "pc_value"
        assert config.get_any_from_config("test_option", "option") == "cmd_value"

    def test_get_any_from_config_pc(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        config.poodle_config.test_option = "pc_value"
        assert config.get_any_from_config("test_option") == "pc_value"


class TestGetStrFromConfig:
    def test_get_str_from_config(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "cmd_value"}
        assert config.get_str_from_config("test_option", "option") == "cmd_value"

    def test_get_str_from_config_none(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = None
        assert config.get_str_from_config("test_option") is None

    def test_get_str_from_config_cast(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = 123
        assert config.get_str_from_config("test_option") == "123"


class TestGetBoolFromConfig:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            (False, False),
            ("TRUE", True),
            ("true", True),
            ("True", True),
            ("FALSE", False),
            ("false", False),
            ("False", False),
            (None, None),
        ],
    )
    def test_get_bool_from_config(self, value, expected):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = value
        assert config.get_bool_from_config("test_option") == expected

    def test_get_bool_from_config_cmd(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {"option": "true"}
        assert config.get_bool_from_config("test_option", "option") is True

    def test_get_bool_from_config_str_err(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = "Yes"
        with pytest.raises(PoodleInputError, match="^test_option from poodle_config.py must be a valid bool$"):
            config.get_bool_from_config("test_option")

    def test_get_bool_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.cmd_kwargs = {}
        config.poodle_config = mock.MagicMock()
        config.poodle_config.test_option = 123
        with pytest.raises(PoodleInputError, match="^test_option from poodle_config.py must be a valid bool$"):
            config.get_bool_from_config("test_option")


class TestGetPathFromConfig:
    def test_get_path_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "test_file.txt"
        assert config.get_path_from_config("test_option") == Path("test_file.txt")

    def test_get_path_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_path_from_config("test_option") == None

    def test_get_path_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = {}
        config.config_file_data = {}
        with pytest.raises(PoodleInputError, match="^test_option from poodle_config.py must be a valid StrPath$"):
            config.get_path_from_config("test_option")


class TestGetIntFromConfig:
    def test_get_int_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "123"
        assert config.get_int_from_config("test_option") == 123

    def test_get_int_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_int_from_config("test_option") == None

    def test_get_int_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "A"
        config.config_file_data = {}
        with pytest.raises(PoodleInputError, match="^test_option from poodle_config.py must be a valid int$"):
            config.get_int_from_config("test_option")


class TestGetFloatFromConfig:
    def test_get_float_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "123.4"
        assert config.get_float_from_config("test_option") == 123.4

    def test_get_float_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_float_from_config("test_option") is None

    def test_get_float_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "A"
        config.config_file_data = {}
        with pytest.raises(PoodleInputError, match="^test_option from poodle_config.py must be a valid float$"):
            config.get_float_from_config("test_option")


class TestGetAnyListFromConfig:
    def test_get_any_list_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = ["test1", 123]
        assert config.get_any_list_from_config("test_option") == ["test1", 123]

    def test_get_any_list_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_any_list_from_config("test_option") is None

    def test_get_any_list_from_config_str(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "test1"
        assert config.get_any_list_from_config("test_option") == ["test1"]

    def test_get_any_list_from_config_set(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = {"test1", 123}
        actual = config.get_any_list_from_config("test_option")
        assert actual == ["test1", 123] or actual == [123, "test1"]

    def test_get_any_list_from_config_value(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = 123
        assert config.get_any_list_from_config("test_option") == [123]


class TestGetStrListFromConfig:
    def test_get_str_list_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = ["test1", 123]
        assert config.get_str_list_from_config("test_option") == ["test1", "123"]

    def test_get_str_list_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_str_list_from_config("test_option") is None

    def test_get_str_list_from_config_str(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "test1"
        assert config.get_str_list_from_config("test_option") == ["test1"]

    def test_get_str_list_from_config_set(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = {"test1", 123}
        actual = config.get_str_list_from_config("test_option")
        assert actual == ["test1", "123"] or actual == ["123", "test1"]

    def test_get_str_list_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = 123
        with pytest.raises(
            PoodleInputError,
            match=r"^test_option from poodle_config.py must be a valid Iterable\[str\]$",
        ):
            config.get_str_list_from_config("test_option")


class TestGetPathListFromConfig:
    def test_get_path_list_from_config(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = ["test1", "123"]
        assert config.get_path_list_from_config("test_option") == [Path("test1"), Path("123")]

    def test_get_path_list_from_config_none(self):
        config = config_base.PoodleConfigBase()
        del config.poodle_config.test_option
        config.config_file_data = {}
        assert config.get_path_list_from_config("test_option") is None

    def test_get_path_list_from_config_path(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = Path("test1")
        assert config.get_path_list_from_config("test_option") == [Path("test1")]

    def test_get_path_list_from_config_str(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = "test1"
        assert config.get_path_list_from_config("test_option") == [Path("test1")]

    def test_get_path_list_from_config_list(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = {"test1", "123"}
        actual = config.get_path_list_from_config("test_option")
        assert actual == [Path("test1"), Path("123")] or actual == [Path("123"), Path("test1")]

    def test_get_path_list_from_config_err(self):
        config = config_base.PoodleConfigBase()
        config.poodle_config.test_option = 123
        with pytest.raises(
            PoodleInputError,
            match=r"^test_option from poodle_config.py must be a valid Iterable\[StrPath\]$",
        ):
            config.get_path_list_from_config("test_option")
