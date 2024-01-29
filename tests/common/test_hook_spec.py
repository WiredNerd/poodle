from __future__ import annotations

import importlib
from unittest import mock

import pytest

from poodle.common import hook_spec
from tests.common.mock_util import DecoratorMock


@pytest.fixture()
def _setup():
    yield
    importlib.reload(hook_spec)


def test_hook_spec_markers():
    with mock.patch("pluggy.HookspecMarker") as mock_hook_spec_marker:
        hookspec = DecoratorMock()
        mock_hook_spec_marker.return_value = hookspec
        importlib.reload(hook_spec)
        mock_hook_spec_marker.assert_called_once_with("poodle")
        assert hookspec.decorator.call_count == 7
        hookspec.decorator.assert_has_calls(
            [
                mock.call("register_plugins", historic=True),
                mock.call("add_options"),
                mock.call("configure"),
                mock.call("create_mutations"),
                mock.call("filter_mutations"),
                mock.call("run_testing", firstresult=True),
                mock.call("report_results"),
            ]
        )
