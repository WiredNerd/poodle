from __future__ import annotations

from unittest import mock

import pytest

from poodle.common.echo_wrapper import EchoWrapper


@pytest.fixture()
def mock_secho():
    with mock.patch("click.secho") as mock_secho:
        yield mock_secho


class TestEchoWrapper:
    def test_echo_wrapper(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=True, echo_no_color=False)
        echo_wrapper("test")
        mock_secho.assert_called_once_with("test", None, True, False, None)

    def test_echo_wrapper_no_color(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=True, echo_no_color=True)
        echo_wrapper("test", color=True)
        mock_secho.assert_called_once_with("test", None, True, False, False)

    def test_echo_wrapper_disabled(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=False, echo_no_color=False)
        echo_wrapper("test")
        mock_secho.assert_not_called()

    def test_echo_wrapper_vars1(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=True, echo_no_color=False)
        echo_wrapper("test", file="file", nl=False, err=True, color=True, style="style")
        mock_secho.assert_called_once_with("test", "file", False, True, True, style="style")

    def test_echo_wrapper_vars2(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=True, echo_no_color=False)
        echo_wrapper("test", file="file", nl=False, err=False, color=True, style="style")
        mock_secho.assert_called_once_with("test", "file", False, False, True, style="style")

    def test_echo_wrapper_vars3(self, mock_secho: mock.MagicMock):
        echo_wrapper = EchoWrapper(echo_enabled=True, echo_no_color=False)
        echo_wrapper("test", file="file", nl=False, err=False, color=False, style="style")
        mock_secho.assert_called_once_with("test", "file", False, False, False, style="style")
