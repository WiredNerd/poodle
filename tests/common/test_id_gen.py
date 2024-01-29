from __future__ import annotations

from poodle.common import id_gen


class TestIdentifierGenerator:
    def test_identifier_generator(self):
        identifier_generator = id_gen.IdentifierGenerator()
        assert identifier_generator() == "1"
        assert identifier_generator() == "2"
        assert identifier_generator() == "3"
