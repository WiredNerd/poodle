from pathlib import Path

from poodle.types.work import PoodleWork

from .test_data import TestPoodleConfig


class TestPoodleWork:
    def test_poodle_work(self):
        work = PoodleWork(config=TestPoodleConfig.create_poodle_config())

        assert work.config.config_file == Path("filename.toml")
        assert work.folder_zips == {}
        assert work.mutators == []
        assert work.next_num() == "1"
        assert work.next_num() == "2"
