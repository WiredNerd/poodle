"""Resolve configuration options and build PoodleConfig object."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import PoodleInputError, poodle_config, tomllib
from .data_types import PoodleConfig

default_log_format = "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
default_log_level = logging.WARN

default_source_folders = [Path("src"), Path("lib")]
default_file_filters = [r"^test_.*\.py", r"_test\.py$"]
default_file_copy_filters = [r"^test_.*\.py", r"_test\.py$", r"^\."]
default_work_folder = Path(".poodle-temp")
default_mutator_opts: dict[str, Any] = {}
default_runner = "command_line"
default_runner_opts: dict[str, Any] = {
    "command_line": "pytest -x --assert=plain -o pythonpath="
}
default_reporters = ["summary", "not_found"]
default_reporter_opts: dict[str, Any] = {}


def build_config(command_line_sources: tuple[Path], config_file: Path | None, verbosity: str | None) -> PoodleConfig:
    """Build PoodleConfig object."""
    config_file_path = get_config_file_path(config_file)
    config_file_data = get_config_file_data(config_file_path)

    log_format = get_str_from_config("log_format", config_file_data, default=default_log_format)
    log_level: int | str = get_any_from_config(
        "log_level",
        config_file_data,
        default=default_log_level,
        command_line=get_cmd_line_log_level(verbosity),
    )
    logging.basicConfig(format=log_format, level=log_level)

    return PoodleConfig(
        config_file=config_file_path,
        source_folders=get_source_folders(command_line_sources, config_file_data),
        file_filters=get_str_list_from_config("file_filters", config_file_data, default=default_file_filters),
        file_copy_filters=get_str_list_from_config(
            "file_copy_filters",
            config_file_data,
            default=default_file_copy_filters,
        ),
        work_folder=get_path_from_config("work_folder", config_file_data, default=default_work_folder),
        log_format=log_format,
        log_level=log_level,
        echo_enabled=get_bool_from_config(
            "echo_enabled",
            config_file_data,
            default=True,
            command_line=get_cmd_line_echo_enabled(verbosity),
        ),
        mutator_opts=get_dict_from_config("mutator_opts", config_file_data, default=default_mutator_opts),
        skip_mutators=get_str_list_from_config("skip_mutators", config_file_data, default=[]),
        add_mutators=get_any_list_from_config("add_mutators", config_file_data),
        runner=get_str_from_config("runner", config_file_data, default=default_runner),
        runner_opts=get_dict_from_config("runner_opts", config_file_data, default=default_runner_opts),
        reporters=get_str_list_from_config("reporters", config_file_data, default=default_reporters),
        reporter_opts=get_dict_from_config("reporter_opts", config_file_data, default=default_reporter_opts),
    )


def get_cmd_line_log_level(verbosity: str | None) -> int | None:
    if verbosity:
        return {
            "q": logging.ERROR,
            "v": logging.INFO,
            "vv": logging.DEBUG,
        }.get(verbosity, None)
    return None


def get_cmd_line_echo_enabled(verbosity: str | None) -> bool | None:
    if verbosity:
        return {
            "q": False,
            "v": True,
            "vv": True,
        }.get(verbosity, None)
    return None


def get_config_file_path(config_file: Path | None) -> Path | None:
    """Identify which configuration file to use.

    Checks in this order, first value is used.
    Command Line, poodle.toml, pyproject.toml.
    Returns None if no config file found.
    """
    if config_file:
        if not config_file.is_file():
            msg = f"Config file not found: --config_file='{config_file}'"
            raise PoodleInputError(msg)
        return config_file

    files = [
        "poodle.toml",
        "pyproject.toml",
    ]  # TODO(wirednerd): ["poodle.toml", "tox.ini", "setup.cfg", "pyproject.toml"]

    for file in files:
        path = Path(file)
        if path.is_file():
            return path

    return None


def get_config_file_data(config_file: Path | None) -> dict:
    """Retrieve Poodle configuration from specified Config File."""
    if not config_file:
        return {}

    if config_file.suffix == ".toml":
        return get_config_file_data_toml(config_file)

    # TODO(wirednerd): tox.ini and setup.cfg
    # https://tox.wiki/en/3.24.5/config.html

    msg = f"Config file type not supported: --config_file='{config_file}'"
    raise PoodleInputError(msg)


def get_config_file_data_toml(config_file: Path) -> dict:
    """Retrieve Poodle configuration from a 'toml' Config File."""
    config_data = tomllib.load(config_file.open(mode="rb"))
    config_data = config_data.get("tool", config_data)
    return config_data.get("poodle", {})


def get_source_folders(command_line_sources: tuple[Path], config_data: dict) -> list[Path]:
    """Retrieve list of source folders that contain files to mutate.

    Verifies that all returned values are existing directories.
    """
    source_folders = get_path_list_from_config(
        option_name="source_folders",
        config_data=config_data,
        command_line=command_line_sources,
        default=[source for source in default_source_folders if source.is_dir()],
    )

    if not source_folders:
        raise PoodleInputError("No source folder found to mutate.")

    for source in source_folders:
        if not source.is_dir():
            msg = f"Source '{source}' must be a folder."
            raise PoodleInputError(msg)

    return source_folders


def get_bool_from_config(
    option_name: str,
    config_data: dict,
    default: bool,
    command_line: bool | str | None = None,
) -> bool:
    """Retrieve Config Option that should be a Boolean.

    Retrieve highest priority value from config sources.
    """
    value, _ = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.upper() == "TRUE"

    return default


def get_path_from_config(
    option_name: str,
    config_data: dict,
    default: Path,
    command_line: Path | None = None,
) -> Path:
    """Retrieve Config Option that should be a String.

    Retrieve highest priority value from config sources.
    """
    value, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not value:
        return default

    try:
        return Path(value)
    except TypeError:
        msg = f"{option_name} from {source} must be a valid StrPath"
        raise PoodleInputError(msg) from None


def get_path_list_from_config(
    option_name: str,
    config_data: dict,
    default: list[Path] | None = None,
    command_line: tuple[Path] | None = None,
) -> list[Path]:
    """Retrieve Config Option that should be a List of Paths.

    Retrieve highest priority value from config sources.
    If input was a single Path, return as a list of Paths.
    Convert input Iterable to List.
    """
    default_fix = default or []
    command_line_fix = command_line or ()

    values, source = get_option_from_config(
        option_name=option_name,
        config_data=config_data,
        command_line=command_line_fix,
    )

    if not values:
        return default_fix

    try:
        if isinstance(values, Path):
            return [values]

        if isinstance(values, str):
            return [Path(values)]

        return [Path(value) for value in values]
    except TypeError:
        msg = f"{option_name} from {source} must be a valid Iterable[StrPath]"
        raise PoodleInputError(msg) from None


def get_any_from_config(
    option_name: str,
    config_data: dict,
    default: Any = None,  # noqa: ANN401
    command_line: Any | None = None,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Retrieve Config Option that can by any type.

    Retrieve highest priority value from config sources.
    """
    value, _ = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not value:
        return default
    return value


def get_any_list_from_config(
    option_name: str,
    config_data: dict,
    default: list[Any] | None = None,
    command_line: tuple[Any] | None = None,
) -> list[Any]:
    """Retrieve Config Option that should be a List of any types.

    Retrieve highest priority value from config sources.
    Convert input Iterable to List.
    """
    default_fix = default or []
    command_line_fix = command_line or ()

    values, _ = get_option_from_config(
        option_name=option_name,
        config_data=config_data,
        command_line=command_line_fix,
    )

    if not values:
        return default_fix

    if isinstance(values, str):
        return [values]

    if isinstance(values, Iterable):
        return list(values)

    return [values]


def get_str_from_config(
    option_name: str,
    config_data: dict,
    default: str = "",
    command_line: str = "",
) -> str:
    """Retrieve Config Option that should be a String.

    Retrieve highest priority value from config sources.
    """
    value, _ = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not value:
        return default

    return str(value)


def get_str_list_from_config(
    option_name: str,
    config_data: dict,
    default: list[str] | None = None,
    command_line: str | tuple[str] | None = None,
) -> list[str]:
    """Retrieve Config Option that should be a List of Strings.

    Retrieve highest priority value from config sources.
    If input was a single string, return as a list of strings.
    Convert input Iterable to List.
    """
    default_fix = default or []
    command_line_fix = command_line or ()

    values, source = get_option_from_config(
        option_name=option_name,
        config_data=config_data,
        command_line=command_line_fix,
    )

    if not values:
        return default_fix

    if isinstance(values, str):
        return [values]

    try:
        return [str(value) for value in values]
    except TypeError:
        msg = f"{option_name} from {source} must be a valid Iterable[str]"
        raise PoodleInputError(msg) from None


def get_option_from_config(
    option_name: str,
    config_data: dict,
    command_line: Any,  # noqa: ANN401
) -> tuple[Any | None, str | None]:
    """Retrieve Config Option of any type.

    Check sources in priority order, and return the first one found.

    Priority Order: Command Line, poodle_config.py, config file

    Returns: Identified Config value, Source Name
    """
    if command_line or command_line == False:
        return command_line, "Command Line"

    if hasattr(poodle_config, option_name):
        return getattr(poodle_config, option_name), "poodle_config.py"

    if option_name in config_data:
        return config_data[option_name], "config file"

    return None, None


def get_dict_from_config(
    option_name: str,
    config_data: dict,
    default: dict | None = None,
    command_line: dict | None = None,
) -> dict:
    """Merge Key-Value pairs from Config sources to a dict.

    Builds dict by starting with values from lowest priority source.
    Then 'updating' them with values from higher priority sources.

    Priority Order: Command Line, poodle_config.py, config file, defaults
    """
    default = default or {}
    command_line = command_line or {}

    option_value = default

    if option_name in config_data:
        try:
            option_value.update(config_data[option_name])
        except ValueError:
            msg = f"{option_name} in config file must be a valid dict"
            raise PoodleInputError(msg) from None

    if hasattr(poodle_config, option_name):
        try:
            option_value.update(getattr(poodle_config, option_name))
        except ValueError:
            msg = f"poodle_config.{option_name} must be a valid dict"
            raise PoodleInputError(msg) from None

    if command_line:
        option_value.update(command_line)

    return option_value
