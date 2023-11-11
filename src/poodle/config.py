"""Resolve configuration options and build PoodleConfig object."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from poodle import PoodleInputError, poodle_config, tomllib
from poodle.data import PoodleConfig

default_source_folders = [Path("src"), Path("lib")]
default_file_filters = [r"^test_.*\.py", r"_test\.py$"]
default_file_copy_filters = [r"^test_.*\.py", r"_test\.py$", r"^\."]
default_work_folder = Path(".poodle-temp")
default_mutator_opts = {}
default_runner_opts = {"command_line": "pytest -x --assert=plain --no-header --no-summary -o pythonpath="}


def build_config(command_line_sources: tuple[Path], config_file: Path | None) -> PoodleConfig:
    """Build PoodleConfig object."""
    config_file_path = get_config_file_path(config_file)
    config_file_data = get_config_file_data(config_file_path)

    return PoodleConfig(
        config_file=config_file_path,
        source_folders=get_source_folders(command_line_sources, config_file_data),
        file_filters=get_str_list_from_config("file_filters", config_file_data, default=default_file_filters),
        file_copy_filters=get_str_list_from_config(
            "file_copy_filters", config_file_data, default=default_file_copy_filters
        ),
        work_folder=get_path_from_config("work_folder", config_file_data, default=default_work_folder),
        mutator_opts=get_dict_from_config("mutator_opts", config_file_data, default=default_mutator_opts),
        skip_mutators=get_str_list_from_config("skip_mutators", config_file_data, default=[]),
        add_mutators=get_any_list_from_config("add_mutators", config_file_data),
        runner_opts=get_dict_from_config("runner_opts", config_file_data, default=default_runner_opts),
    )


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


def get_path_from_config(
    option_name: str,
    config_data: dict,
    default: Path | None = None,
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
) -> Path:
    """Retrieve Config Option that should be a List of Paths.

    Retrieve highest priority value from config sources.
    If input was a single Path, return as a list of Paths.
    Convert input Iterable to List.
    """
    default = default or []
    command_line = command_line or ()

    values, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not values:
        return default

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
    default: any = None,
    command_line: any = None,
) -> any:
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
    default: list[any] | None = None,
    command_line: tuple[any] | None = None,
) -> list[any]:
    """Retrieve Config Option that should be a List of any types.

    Retrieve highest priority value from config sources.
    Convert input Iterable to List.
    """
    default = default or []
    command_line = command_line or ()

    values, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not values:
        return default

    if isinstance(values, str):
        return [values]

    if isinstance(values, Iterable):
        return [value for value in values]

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
    default = default or []
    command_line = command_line or ()

    values, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if not values:
        return default

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
    command_line: any,
) -> tuple[any, str]:
    """Retrieve Config Option of any type.

    Check sources in priority order, and return the first one found.

    Priority Order: Command Line, poodle_config.py, config file

    Returns: Identified Config value, Source Name
    """
    if command_line:
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
