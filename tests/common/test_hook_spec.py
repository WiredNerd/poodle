from __future__ import annotations

import importlib
from unittest import mock

import pytest
from mock_decorator import MockDecorator

from poodle.common import hook_spec


@pytest.fixture()
def _setup():
    yield
    importlib.reload(hook_spec)


def test_hook_spec_markers():
    with mock.patch("pluggy.HookspecMarker") as mock_hook_spec_marker:
        hookspec = MockDecorator()
        mock_hook_spec_marker.return_value = hookspec
        importlib.reload(hook_spec)
        mock_hook_spec_marker.assert_called_once_with("poodle")

        hookspec.register_plugins.assert_called_once_with(historic=True)
        hookspec.add_options.assert_called_once_with()
        hookspec.configure.assert_called_once_with()
        hookspec.create_mutations.assert_called_once_with()
        hookspec.filter_mutations.assert_called_once_with()
        hookspec.run_testing.assert_called_once_with(firstresult=True)
        hookspec.report_results.assert_called_once_with()


def test_coverage():
    assert hook_spec.register_plugins(None) == None
    assert hook_spec.add_options(None) == None
    assert hook_spec.configure(None, None, None, None) == None
    assert hook_spec.create_mutations(None, None, None, None) == None
    assert hook_spec.filter_mutations(None, None, None) == None
    assert hook_spec.run_testing(None, None, None, None, None, None) == None
    assert hook_spec.report_results(None, None, None) == None
