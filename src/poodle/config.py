"""Resolve configuration options and build PoodleConfig object."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from mergedeep import merge  # type: ignore[import-untyped]
from wcmatch import glob

from . import PoodleInputError, poodle_config, tomllib
from .data_types import PoodleConfig

default_source_folders = [Path("src"), Path("lib")]

default_log_format = "%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
default_log_level = logging.WARN

default_file_flags = glob.GLOBSTAR | glob.NODIR
default_file_filters = ["test_*.py", "*_test.py", "poodle_config.py", "setup.py"]
default_file_copy_flags = glob.GLOBSTAR | glob.NODIR
default_file_copy_filters = ["__pycache__/**"]
default_work_folder = Path(".poodle-temp")

default_min_timeout = 10
default_timeout_multiplier = 10
default_runner = "command_line"

default_reporters = ["summary", "not_found"]


def default_max_workers() -> int:
    """Calculate Default for max_workers as one less than available processors."""
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0)) - 1
    cpu_count = os.cpu_count() or 1  # nomut: Number
    if cpu_count > 1:
        return cpu_count - 1
    return cpu_count


def build_config(  # noqa: PLR0913
    cmd_sources: tuple[Path],
    cmd_config_file: Path | None,
    cmd_quiet: int,
    cmd_verbose: int,
    cmd_max_workers: int | None,
    cmd_excludes: tuple[str],
    cmd_only_files: tuple[str],
    cmd_report: tuple[str],
    cmd_html: Path | None,
    cmd_json: Path | None,
    cmd_fail_under: float | None,
) -> PoodleConfig:
    """Build PoodleConfig object."""
    config_file_path = get_config_file_path(cmd_config_file)
    config_file_data = get_config_file_data(config_file_path)
    project_name, project_version = get_project_info(config_file_path)

    log_format = get_str_from_config("log_format", config_file_data, default=default_log_format)
    log_level: int | str = get_any_from_config(
        "log_level",
        config_file_data,
        default=default_log_level,
        command_line=get_cmd_line_log_level(cmd_quiet, cmd_verbose),
    )
    logging.basicConfig(format=log_format, level=log_level)

    file_filters = get_str_list_from_config("file_filters", config_file_data, default=default_file_filters)
    # TODO: append file excludes and append py excludes
    # file_filters += get_str_list_from_config("exclude", config_file_data, default=[]) # noqa: ERA001
    file_filters += cmd_excludes

    cmd_reporter_opts: dict[str, Any] = {}
    if cmd_html:
        merge(cmd_reporter_opts, {"html": {"report_folder": cmd_html}})
    if cmd_json:
        merge(cmd_reporter_opts, {"json_report_file": cmd_json})

    return PoodleConfig(
        project_name=get_str_from_config("project_name", config_file_data, default=project_name),
        project_version=get_str_from_config("project_version", config_file_data, default=project_version),
        config_file=config_file_path,
        source_folders=get_source_folders(cmd_sources, config_file_data),
        only_files=get_str_list_from_config("only_files", config_file_data, default=[], command_line=cmd_only_files),
        file_flags=get_int_from_config("file_flags", config_file_data, default=default_file_flags),
        file_filters=file_filters,
        file_copy_flags=get_int_from_config("file_copy_flags", config_file_data, default=default_file_copy_flags),
        file_copy_filters=get_str_list_from_config(
            "file_copy_filters",
            config_file_data,
            default=default_file_copy_filters,
        ),
        work_folder=get_path_from_config("work_folder", config_file_data, default=default_work_folder),
        max_workers=get_int_from_config(
            "max_workers",
            config_file_data,
            default=default_max_workers(),
            command_line=cmd_max_workers,
        ),
        log_format=log_format,
        log_level=log_level,
        echo_enabled=get_bool_from_config(
            "echo_enabled",
            config_file_data,
            default=True,
            command_line=get_cmd_line_echo_enabled(cmd_quiet),
        ),
        echo_no_color=get_bool_from_config("echo_no_color", config_file_data),
        mutator_opts=get_dict_from_config("mutator_opts", config_file_data),
        skip_mutators=get_str_list_from_config("skip_mutators", config_file_data, default=[]),
        add_mutators=get_any_list_from_config("add_mutators", config_file_data),
        min_timeout=get_int_from_config("min_timeout", config_file_data) or default_min_timeout,
        timeout_multiplier=get_int_from_config("timeout_multiplier", config_file_data) or default_timeout_multiplier,
        runner=get_str_from_config("runner", config_file_data, default=default_runner),
        runner_opts=get_dict_from_config("runner_opts", config_file_data),
        reporters=get_reporters(config_file_data, cmd_report, cmd_html, cmd_json),
        reporter_opts=get_dict_from_config("reporter_opts", config_file_data, command_line=cmd_reporter_opts),
        fail_under=get_float_from_config("fail_under", config_file_data, command_line=cmd_fail_under),
    )


def get_reporters(
    config_file_data: dict,
    cmd_report: tuple[str],
    cmd_html: Path | None,
    cmd_json: Path | None,
) -> list[str]:
    """Retrieve list of reporters to use."""
    reporters = get_str_list_from_config("reporters", config_file_data, default=default_reporters)
    reporters += [reporter for reporter in cmd_report if reporter not in reporters]
    if cmd_html:
        reporters.append("html")
    if cmd_json:
        reporters.append("json")
    return reporters


def get_cmd_line_log_level(cmd_quiet: int, cmd_verbose: int) -> int | None:
    """Map verbosity input to logging level."""
    if cmd_quiet >= 3:
        return logging.CRITICAL
    if cmd_quiet == 2:
        return logging.ERROR
    if cmd_quiet == 1:
        return logging.WARN

    if cmd_verbose >= 3:
        return logging.NOTSET
    if cmd_verbose == 2:
        return logging.DEBUG
    if cmd_verbose == 1:
        return logging.INFO

    return None


def get_cmd_line_echo_enabled(cmd_quiet: int) -> bool | None:
    """Map verbosity input to enable/disable echo statements."""
    if cmd_quiet == 0:
        return None
    return False


def get_config_file_path(config_file: Path | None) -> Path | None:
    """Identify which configuration file to use.

    Checks in this order, first value is used.
    Command Line, poodle.toml, pyproject.toml.
    Returns None if no config file found.
    """
    if config_file:
        if not config_file.is_file():
            msg = f"Config file not found: '{config_file}'"
            raise PoodleInputError(msg)
        return config_file

    if hasattr(poodle_config, "config_file"):
        config_file = Path(poodle_config.config_file)
        if not config_file.is_file():
            msg = f"config_file not found: '{poodle_config.config_file}'"
            raise PoodleInputError(msg)
        return config_file

    files = [
        "poodle.toml",
        "pyproject.toml",
    ]  # TODO: ["poodle.toml", "tox.ini", "setup.cfg", "pyproject.toml"]

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

    # TODO: tox.ini and setup.cfg
    # https://tox.wiki/en/3.24.5/config.html

    msg = f"Config file type not supported: --config_file='{config_file}'"
    raise PoodleInputError(msg)


def get_project_info(config_file: Path | None) -> tuple[str, str]:
    """Retrieve Poodle configuration from specified Config File."""
    if not config_file:
        return ("", "")

    if config_file.suffix == ".toml":
        return get_project_info_toml(config_file)

    # TODO: tox.ini and setup.cfg
    # https://tox.wiki/en/3.24.5/config.html

    msg = f"Config file type not supported: --config_file='{config_file}'"
    raise PoodleInputError(msg)


def get_config_file_data_toml(config_file: Path) -> dict:
    """Retrieve Poodle configuration from a 'toml' Config File."""
    try:
        config_data = tomllib.load(config_file.open(mode="rb"))
        config_data: dict = config_data.get("tool", config_data)  # type: ignore[no-redef]
        return config_data.get("poodle", {})
    except tomllib.TOMLDecodeError as err:
        msgs = [f"Error decoding toml file: {config_file}"]
        msgs.extend(err.args)
        raise PoodleInputError(*msgs) from None


def get_project_info_toml(config_file: Path) -> tuple[str, str]:
    """Retrieve Project Name and Version from a 'toml' Config File."""
    try:
        config_data = tomllib.load(config_file.open(mode="rb"))
        config_data: dict = config_data.get("project", config_data)  # type: ignore[no-redef]
        return config_data.get("name", ""), config_data.get("version", "")
    except tomllib.TOMLDecodeError:
        return "", ""


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
    default: bool | None = None,
    command_line: bool | str | None = None,
) -> bool | None:
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

    if value is None:
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

    if values is None:
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

    if value is None:
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

    if values is None:
        return default_fix

    if isinstance(values, str):
        return [values]

    if isinstance(values, Iterable):
        return list(values)

    return [values]


def get_int_from_config(
    option_name: str,
    config_data: dict,
    default: int | None = None,
    command_line: int | None = None,
) -> int | None:
    """Retrieve Config Option that should be an int or None.

    Retrieve highest priority value from config sources.
    """
    value, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        msg = f"{option_name} from {source} must be a valid int"
        raise PoodleInputError(msg) from None


def get_float_from_config(
    option_name: str,
    config_data: dict,
    default: float | None = None,
    command_line: float | None = None,
) -> float | None:
    """Retrieve Config Option that should be an float or None.

    Retrieve highest priority value from config sources.
    """
    value, source = get_option_from_config(option_name=option_name, config_data=config_data, command_line=command_line)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        msg = f"{option_name} from {source} must be a valid float"
        raise PoodleInputError(msg) from None


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

    if value is None:
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

    if values is None:
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
    if command_line or command_line is False:
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
            merge(option_value, config_data[option_name])
        except TypeError:
            msg = f"{option_name} in config file must be a valid dict"
            raise PoodleInputError(msg) from None

    if hasattr(poodle_config, option_name):
        try:
            merge(option_value, getattr(poodle_config, option_name))
        except TypeError:
            msg = f"poodle_config.{option_name} must be a valid dict"
            raise PoodleInputError(msg) from None

    if command_line:
        merge(option_value, command_line)

    return option_value
