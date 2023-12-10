from unittest import mock

from poodle.data_types.work import EchoWrapper, PoodleWork
from tests.data_types.test_data import PoodleConfigStub


class TestPoodleWork:
    def test_poodle_work(self):
        config = PoodleConfigStub(echo_enabled=True, echo_no_color=True)
        work = PoodleWork(config=config)

        assert work.config == config
        assert work.folder_zips == {}
        assert work.mutators == []
        assert work.runner() is None
        assert work.reporters == []
        assert work._echo_wrapper.echo_enabled is True
        assert work._echo_wrapper.echo_no_color is True

        assert work.echo == work._echo_wrapper.echo

        assert work.next_num() == "1"
        assert work.next_num() == "2"


class TestEchoWrapper:
    @mock.patch("poodle.data_types.work.click")
    def test_echo(self, click):
        wrap = EchoWrapper(True, False)
        file = mock.MagicMock()
        wrap.echo("test", file=file, nl=False, err=True, fg="black")
        click.secho.assert_called_with("test", file, False, True, None, fg="black")

    @mock.patch("poodle.data_types.work.click")
    def test_echo_no_color(self, click):
        wrap = EchoWrapper(True, True)
        wrap.echo("test")
        click.secho.assert_called_with("test", None, True, False, False)

    @mock.patch("poodle.data_types.work.click")
    def test_echo_no_echo(self, click):
        wrap = EchoWrapper(False, True)
        wrap.echo("test")
        click.secho.assert_not_called()
