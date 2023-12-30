from unittest import mock

import pytest

from poodle import report
from poodle.reporters import report_not_found, report_summary
from tests.data_types.test_data import PoodleConfigStub


@pytest.fixture()
def mock_logger():
    with mock.patch("poodle.report.logger") as logger:
        yield logger


def test_logger():
    assert report.logger.name == "poodle.report"


class TestReporters:
    def test_builtin_reporters(self):
        assert report.builtin_reporters == {
            "summary": report_summary,
            "not_found": report_not_found,
            "json": report.report_json,
            "html": report.report_html,
        }

    def test_generate_reporters(self, mock_logger: mock.MagicMock):
        config = PoodleConfigStub(
            reporters=["summary", "not_found", "poodle.reporters.report_summary"],
        )
        gen_report = report.generate_reporters(config)

        assert next(gen_report) is report_summary
        mock_logger.debug.assert_called_with("Reporters: %s", config.reporters)

        assert next(gen_report) is report_not_found
        assert next(gen_report) is report_summary
        with pytest.raises(StopIteration):
            next(gen_report)
