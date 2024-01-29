from __future__ import annotations

from collections import OrderedDict
from typing import Any


class PoodleOptionCollector:
    cli_options = []
    file_options = OrderedDict()
    hidden_options = OrderedDict()
    group_descriptions = {}

    def add_cli_option(self, *param_decls: str, cls: type | None = None, **attrs: Any) -> None:
        """Add Command Line Option.

        :param param_decls: Option names.
        :param cls: Option class.
        :param attrs: Option attributes.

        See click.option decorator for more information."""
        self.cli_options.append({"param_decls": param_decls, "cls": cls, "attrs": attrs})

    def add_file_option(self, field_name, description, group=None, hidden=False) -> None:
        """Add File Option to Help Text.

        :param field_name: Name of field in config file or poodle_config.py module.
        :param description: Description of option.
        :param group: Group name, if any."""
        options = self.file_options if not hidden else self.hidden_options
        if group:
            if group not in options:
                options[group] = OrderedDict()
            options[group][field_name] = description
        else:
            options[field_name] = description

    def add_group_description(self, group_name: str, description: str) -> None:
        """Add Group Description to Help Text.

        :param group_name: Name of group.
        :param description: Description of group."""
        self.group_descriptions[group_name] = description

    def click_epilog_from_plugins(self):
        epilog = "\b"

        pad = self.longest_field_size(self.file_options.keys()) + 2

        for field_name, description in reversed(self.file_options.items()):
            if isinstance(description, dict):
                if not epilog.endswith("\b"):
                    epilog += "\n\b"
                epilog += self.click_epilog_for_group(field_name, description)
            else:
                epilog += f"\n{field_name + ':':<{pad}}{description}"

        return epilog

    def click_epilog_for_group(self, group: str, fields: dict) -> str:
        indent = 2
        pad = max(self.longest_field_size(fields.keys()) + indent, len(group)) + 2

        epilog = f"\n{group + ':':<{pad}}{self.group_descriptions.get(group, '')}"
        for field_name, description in fields.items():
            field_name_out = (" " * indent) + field_name + ":"
            epilog += f"\n{field_name_out:<{pad}}{description}"

        epilog += "\n\b"
        return epilog

    @staticmethod
    def longest_field_size(fields: list[str]) -> int:
        """Return the longest field size."""
        return max(len(field) for field in fields)
