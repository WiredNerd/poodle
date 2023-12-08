import click

from poodle.data_types.work import PoodleWork

from .test_data import TestPoodleConfig


class TestPoodleWork:
    def test_poodle_work(self):
        config = TestPoodleConfig.create_poodle_config()
        work = PoodleWork(config=config)

        assert work.config == config
        assert work.folder_zips == {}
        assert work.mutators == []
        assert work.runner() is None
        assert work.reporters == []
        assert work.echo == click.echo

        assert work.next_num() == "1"
        assert work.next_num() == "2"

    def test_poodle_work_no_echo(self):
        config = TestPoodleConfig.create_poodle_config()
        config.echo_enabled = False

        work = PoodleWork(config=config)
        assert work.echo != click.echo
        assert work.echo() is None
