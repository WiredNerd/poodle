from __future__ import annotations

from collections import OrderedDict
from unittest import mock

import pytest

from poodle.common.option_collector import PoodleOptionCollector


class TestPoodleOptionCollector:
    def test_init(self):
        poodle_option_collector = PoodleOptionCollector()
        assert poodle_option_collector.cli_options == []
        assert poodle_option_collector.file_options == OrderedDict()
        assert poodle_option_collector.hidden_options == OrderedDict()
        assert poodle_option_collector.group_descriptions == {}

    def test_add_cli_option(self):
        poodle_option_collector = PoodleOptionCollector()
        assert poodle_option_collector.cli_options == []
        poodle_option_collector.add_cli_option("minimum", "min")
        poodle_option_collector.add_cli_option("maximum", cls=int, help="max value")
        assert poodle_option_collector.cli_options == [
            {"param_decls": ("minimum", "min"), "cls": None, "attrs": {}},
            {"param_decls": ("maximum",), "cls": int, "attrs": {"help": "max value"}},
        ]

    def populate_file_options(self, poodle_option_collector: PoodleOptionCollector):
        poodle_option_collector.add_file_option("minimum", "min value", group="speed")
        poodle_option_collector.add_file_option("maximum", "max value", group="speed", hidden=False)
        poodle_option_collector.add_file_option("average", "avg value")
        poodle_option_collector.add_file_option("skip", "skip value", hidden=True)

    def test_add_file_option(self):
        poodle_option_collector = PoodleOptionCollector()
        assert poodle_option_collector.file_options == {}
        self.populate_file_options(poodle_option_collector)
        assert poodle_option_collector.file_options == {
            "speed": {"minimum": "min value", "maximum": "max value"},
            "average": "avg value",
        }
        assert poodle_option_collector.hidden_options == {"skip": "skip value"}

    def test_add_file_option_ordered(self):
        poodle_option_collector = PoodleOptionCollector()
        assert poodle_option_collector.file_options == {}
        self.populate_file_options(poodle_option_collector)

        assert isinstance(poodle_option_collector.file_options, OrderedDict)
        assert isinstance(poodle_option_collector.file_options["speed"], OrderedDict)
        assert isinstance(poodle_option_collector.hidden_options, OrderedDict)

    def test_add_group_description(self):
        poodle_option_collector = PoodleOptionCollector()
        poodle_option_collector.add_group_description("speed", "speed options")
        assert poodle_option_collector.group_descriptions == {"speed": "speed options"}

    def test_click_epilog_from_plugins(self):
        poodle_option_collector = PoodleOptionCollector()
        poodle_option_collector.add_file_option("poodle", "poodle count", group="dogs")
        poodle_option_collector.add_file_option("yorkie", "yorkie count", group="dogs")
        self.populate_file_options(poodle_option_collector)
        poodle_option_collector.add_group_description("speed", "speed options")
        epilog = (
            "\b"
            "\naverage: avg value"
            "\n\b"
            "\nspeed:     speed options"
            "\n  minimum: min value"
            "\n  maximum: max value"
            "\n\b"
            "\ndogs:     "
            "\n  poodle: poodle count"
            "\n  yorkie: yorkie count"
            "\n\b"
        )
        assert poodle_option_collector.click_epilog_from_plugins() == epilog

    def test_click_epilog_for_group(self):
        poodle_option_collector = PoodleOptionCollector()
        poodle_option_collector.add_group_description("speed", "speed options")
        fields = {"forward": "front gear", "rev": "back gear"}
        epilog = "\nspeed:     speed options" "\n  forward: front gear" "\n  rev:     back gear" "\n\b"
        assert poodle_option_collector.click_epilog_for_group("speed", fields) == epilog

    def test_click_epilog_for_group_no_description(self):
        poodle_option_collector = PoodleOptionCollector()
        fields = {"forward": "front gear", "rev": "back gear"}
        epilog = "\nspeed:     " "\n  forward: front gear" "\n  rev:     back gear" "\n\b"
        assert poodle_option_collector.click_epilog_for_group("speed", fields) == epilog

    def test_longest_field_size(self):
        poodle_option_collector = PoodleOptionCollector()
        assert poodle_option_collector.longest_field_size(["a" * 10, "b" * 12, "c" * 5]) == 12
        assert PoodleOptionCollector.longest_field_size(["a" * 10, "b" * 12, "c" * 5]) == 12
