"""Superclass for Poodle Configuration."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import Any

from mergedeep import merge  # type: ignore[import-untyped]

from .exceptions import PoodleInputError
from .util import get_poodle_config

try:
    import tomllib  # type: ignore [import-not-found]
except ModuleNotFoundError:  # < py3.11
    import tomli as tomllib  # type: ignore [no-redef]


class PoodleConfigBase:
    """Superclass for Poodle Configuration.

    Contains properties and methods used for retrieving configuration options."""

    def __init__(self, cmd_kwargs: dict = {}) -> None:
        """Initialize Poodle Configuration."""
        self.cmd_kwargs = cmd_kwargs
        self.poodle_config = get_poodle_config()

    @cached_property
    def config_file(self) -> Path | None:
        """Property: Key/Value Configuration File.

        Searches in this order, first value is used.
        Command Line, poodle.toml, pyproject.toml.
        Returns None if no config file found.
        """
        cmd_config_file = self.cmd_kwargs.get("config_file")
        if isinstance(cmd_config_file, Path):
            if not cmd_config_file.is_file():
                msg = f"Config file not found: '{cmd_config_file}'"
                raise PoodleInputError(msg)
            return cmd_config_file

        if hasattr(self.poodle_config, "config_file"):
            pc_config_file = Path(self.poodle_config.config_file)
            if not pc_config_file.is_file():
                msg = f"poodle_config.config_file not found: '{self.poodle_config.config_file}'"
                raise PoodleInputError(msg)
            return pc_config_file

        files = [
            "poodle.toml",
            "pyproject.toml",
        ]  # TODO: ["poodle.toml", "tox.ini", "setup.cfg", "pyproject.toml"]

        for file in files:
            path = Path(file)
            if path.is_file():
                return path

        return None

    @cached_property
    def config_file_data(self) -> dict:
        """Poodle configuration data from Key/Value Config File."""
        if not self.config_file:
            return {}

        if self.config_file.suffix == ".toml":
            return self._get_config_file_data_toml()

        # TODO: tox.ini and setup.cfg
        # https://tox.wiki/en/3.24.5/config.html

        msg = f"Config file type not supported: '{self.config_file}'"
        raise PoodleInputError(msg)

    def _get_config_file_data_toml(self) -> dict:
        """Retrieve Poodle configuration from a 'toml' Config File."""
        try:
            config_data = tomllib.load(self.config_file.open(mode="rb"))
            config_data: dict = config_data.get("tool", config_data)  # type: ignore[no-redef]
            return config_data.get("poodle", {})
        except tomllib.TOMLDecodeError as err:
            msgs = [f"Error decoding toml file: '{self.config_file}'"]
            msgs.extend(err.args)
            raise PoodleInputError(*msgs) from None

    @cached_property
    def _pyproject_toml(self) -> dict:
        """Retrieve data from pyproject.toml if present."""
        file = Path("pyproject.toml")
        if file.is_file():
            with suppress(tomllib.TOMLDecodeError):
                return tomllib.load(file.open(mode="rb"))
        return {}

    def merge_dict_from_config(self, option_name: str, defaults: dict = {}) -> dict:
        """Merge Key-Value pairs from Config sources to a dict.

        Builds dict by starting with values from lowest priority source.
        Then 'updating' them with values from higher priority sources.

        Priority Order: poodle_config.py, config file, defaults
        """
        option_value = defaults

        if option_name in self.config_file_data:
            try:
                merge(option_value, self.config_file_data[option_name])
            except TypeError:
                msg = f"{option_name} in config file {self.config_file} must be a valid dict"
                raise PoodleInputError(msg) from None

        if hasattr(self.poodle_config, option_name):
            try:
                merge(option_value, getattr(self.poodle_config, option_name))
            except TypeError:
                msg = f"{option_name} in poodle_config.py must be a valid dict"
                raise PoodleInputError(msg) from None

        return option_value

    def get_option_from_config(
        self,
        option_name: str,
        cmd_option_name: str | None = None,
    ) -> tuple[Any | None, str | None]:
        """Retrieve Config Option of any type.

        Check sources in priority order, and return the first one found.

        Priority Order: Command Line, poodle_config.py, config file

        Returns: Identified Config value, Source Name
        """
        if (
            cmd_option_name
            and cmd_option_name in self.cmd_kwargs
            and (self.cmd_kwargs[cmd_option_name] or self.cmd_kwargs[cmd_option_name] is False)
        ):
            return self.cmd_kwargs[cmd_option_name], "Command Line"

        if hasattr(self.poodle_config, option_name):
            return getattr(self.poodle_config, option_name), "poodle_config.py"

        if option_name in self.config_file_data:
            return self.config_file_data[option_name], "config file"

        return None, None

    def get_any_from_config(self, option_name: str, cmd_option_name: str | None = None) -> Any:  # noqa: ANN401
        """Retrieve Config Option that can by any type."""
        return self.get_option_from_config(option_name, cmd_option_name)[0]

    def get_str_from_config(self, option_name: str, cmd_option_name: str | None = None) -> str | None:
        """Retrieve Config Option that should be a String."""
        value, _ = self.get_option_from_config(option_name, cmd_option_name)

        if value is None:
            return None

        return str(value)

    def get_bool_from_config(self, option_name: str, cmd_option_name: str | None = None) -> bool | None:
        """Retrieve Config Option that should be a bool."""
        value, source = self.get_option_from_config(option_name, cmd_option_name)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.upper() == "TRUE":
                return True
            elif value.upper() == "FALSE":
                return False
            else:
                msg = f"{option_name} from {source} must be a valid bool"
                raise PoodleInputError(msg) from None

        if value is None:
            return None

        msg = f"{option_name} from {source} must be a valid bool"
        raise PoodleInputError(msg) from None

    def get_path_from_config(self, option_name: str, cmd_option_name: str | None = None) -> Path | None:
        """Retrieve Config Option that should be a StrPath."""
        value, source = self.get_option_from_config(option_name, cmd_option_name)

        if value is None:
            return None

        try:
            return Path(value)
        except TypeError:
            msg = f"{option_name} from {source} must be a valid StrPath"
            raise PoodleInputError(msg) from None

    def get_int_from_config(self, option_name: str, cmd_option_name: str | None = None) -> int | None:
        """Retrieve Config Option that should be an int."""
        value, source = self.get_option_from_config(option_name, cmd_option_name)

        if value is None:
            return None

        try:
            return int(value)
        except ValueError:
            msg = f"{option_name} from {source} must be a valid int"
            raise PoodleInputError(msg) from None

    def get_float_from_config(self, option_name: str, cmd_option_name: str | None = None) -> float | None:
        """Retrieve Config Option that should be a float."""
        value, source = self.get_option_from_config(option_name, cmd_option_name)

        if value is None:
            return None

        try:
            return float(value)
        except ValueError:
            msg = f"{option_name} from {source} must be a valid float"
            raise PoodleInputError(msg) from None

    def get_any_list_from_config(self, option_name: str, cmd_option_name: str | None = None) -> list[Any] | None:
        """Retrieve Config Option that should be a List of any types."""
        values = self.get_any_from_config(option_name, cmd_option_name)

        if values is None:
            return None

        if isinstance(values, str):
            return [values]

        if isinstance(values, Iterable):
            return list(values)

        return [values]

    def get_str_list_from_config(self, option_name: str, cmd_option_name: str | None = None) -> list[str] | None:
        """Retrieve Config Option that should be a List of Strings."""

        values, source = self.get_option_from_config(option_name, cmd_option_name)

        if values is None:
            return None

        if isinstance(values, str):
            return [values]

        try:
            return [str(value) for value in values]
        except TypeError:
            msg = f"{option_name} from {source} must be a valid Iterable[str]"
            raise PoodleInputError(msg) from None

    def get_path_list_from_config(self, option_name: str, cmd_option_name: str | None = None) -> list[Path] | None:
        """Retrieve Config Option that should be a List of Paths."""
        values, source = self.get_option_from_config(option_name, cmd_option_name)

        if values is None:
            return None

        if isinstance(values, (Path, str)):
            return [Path(values)]

        try:
            return [Path(value) for value in values]
        except TypeError:
            msg = f"{option_name} from {source} must be a valid Iterable[StrPath]"
            raise PoodleInputError(msg) from None
