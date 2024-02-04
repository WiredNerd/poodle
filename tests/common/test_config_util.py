from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from poodle.common import config_util
import sys
import importlib

m_name = config_util.__name__

@pytest.fixture(autouse=True)
def _reset() -> None:
    importlib.reload(config_util)
    yield
    importlib.reload(config_util)


@pytest.fixture()
def mock_import_module():
    with mock.patch(f"{m_name}.importlib.import_module") as mock_import_module:
        yield mock_import_module


class TestGetPoodleConfig:
    def test_in_sys_modules(self):
        poodle_config = mock.MagicMock()
        mock_sys = mock.MagicMock()
        mock_sys.path = []
        mock_sys.modules = {"poodle_config": poodle_config}
        with mock.patch.object(config_util, "sys", mock_sys):
            assert config_util.get_poodle_config() == poodle_config

    def test_add_cwd_to_sys_path(self, mock_import_module: mock.MagicMock):
        cwd_path = str(Path.cwd())
        poodle_config = mock.MagicMock()
        mock_import_module.return_value = poodle_config

        mock_sys = mock.MagicMock()
        mock_sys.path = ["some_path"]
        mock_sys.modules = {}
        with mock.patch.object(config_util, "sys", mock_sys):
            config_util.get_poodle_config()
        mock_import_module.assert_any_call("poodle_config")
        assert mock_sys.path == ["some_path", cwd_path]

    def test_cwd_in_sys_path(self, mock_import_module: mock.MagicMock):
        cwd_path = str(Path.cwd())
        poodle_config = mock.MagicMock()
        mock_import_module.return_value = poodle_config

        mock_sys = mock.MagicMock()
        mock_sys.path = ["some_path", cwd_path]
        mock_sys.modules = {}
        with mock.patch.object(config_util, "sys", mock_sys):
            config_util.get_poodle_config()
        mock_import_module.assert_any_call("poodle_config")
        assert mock_sys.path == ["some_path", cwd_path]

    def test_module_not_found(self, mock_import_module: mock.MagicMock):
        mock_import_module.side_effect = ModuleNotFoundError("poodle_config")
        mock_sys = mock.MagicMock()
        mock_sys.path = []
        mock_sys.modules = {}
        with mock.patch.object(config_util, "sys", mock_sys):
            assert config_util.get_poodle_config() is None

    def test_cache(self, mock_import_module: mock.MagicMock):
        poodle_config = mock.MagicMock()
        mock_import_module.return_value = poodle_config

        mock_sys = mock.MagicMock()
        mock_sys.path = []
        mock_sys.modules = {}
        with mock.patch.object(config_util, "sys", mock_sys):
            assert config_util.get_poodle_config() == poodle_config
            assert config_util.get_poodle_config() == poodle_config
        assert mock_import_module.call_count == 1
