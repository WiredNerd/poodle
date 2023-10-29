import tomllib
from contextlib import suppress
from pathlib import Path

from poodle.data import PoodleConfig

poodle_config: any = None
with suppress(ImportError):
    import poodle_config  # type: ignore

config_defaults = {
    "source_folders": [Path("src"), Path("lib")],
    "file_filters": ["^test_", "_test$"],
    "work_folder": Path(".poodle-temp"),
    "runner_cmd": "pytest --assert=plain -o pythonpath=",
}


def build_config(source: tuple[str], config_file: str):
    (config_file, config_file_data) = get_config_file_data(config_file)

    return PoodleConfig(
        config_file=config_file,
        source_folders=get_source_folders(source, config_file_data),
        file_filters=config_defaults["file_filters"],
        work_folder=config_defaults["work_folder"],
        runner_cmd=config_defaults["runner_cmd"],
        mutator_opts=get_mutator_opts_from_config(config_file_data),
    )


def get_config_file_data(config_file: str) -> tuple([str | dict]):
    if config_file:
        if not Path(config_file).is_file():
            raise ValueError("--config_file", "Config file not found: " + config_file)
        return config_file, get_config_file_toml(config_file)
        ## TODO tox.ini and setup.cfg

    if Path("poodle.toml").is_file():
        return "poodle.toml", get_config_file_toml("poodle.toml")

    if Path("pyproject.toml").is_file():
        return "pyproject.toml", get_config_file_toml("pyproject.toml")
        # TODO if no data found, try tox.ini and setup.cfg
        # https://tox.wiki/en/3.24.5/config.html

    return None, {}


def get_config_file_toml(config_file: str):
    config_data = tomllib.load(Path(config_file).open(mode="rb"))
    config_data = config_data.get("tool", config_data)
    config_data = config_data.get("poodle", {})
    return config_data


def get_source_folders(source, config_file):
    source_folders = get_source_folders_from_config(source, config_file)

    if not source_folders:
        raise ValueError("No source folder found to mutate")

    for source in source_folders:
        if not source.is_dir():
            raise ValueError("Source must be a folder", str(source))

    return source_folders


def get_source_folders_from_config(sources: tuple[str], config_file: dict) -> list[Path]:
    if sources:
        return [Path(source) for source in sources]

    if hasattr(poodle_config, "source_folders"):
        return [Path(source) for source in getattr(poodle_config, "source_folders")]

    if "source_folders" in config_file:
        return [Path(source) for source in config_file["source_folders"]]

    return [source for source in config_defaults["source_folders"] if source.is_dir()]


def get_mutator_opts_from_config(config_file: dict) -> dict:
    if hasattr(poodle_config, "mutator_opts"):
        return poodle_config.mutator_opts

    if "mutator_opts" in config_file:
        return config_file["mutator_opts"]

    return {}
