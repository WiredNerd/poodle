"""Manage Plugins."""

from __future__ import annotations

import click
import pluggy

from .common import base, hook_spec
from .common.util import get_poodle_config as get_poodle_config
from .mutators import mutator_plugins
from .reporters import reporter_plugins

plugin_manager = pluggy.PluginManager("poodle")
opt_collector = hook_spec.PoodleOptionCollector()


def register_plugins():
    plugin_manager.add_hookspecs(hook_spec)
    plugin_manager.hook.register_plugins.call_historic(kwargs={"plugin_manager": plugin_manager})

    for plugin in mutator_plugins:
        plugin_manager.register(plugin)

    for plugin in reporter_plugins:
        plugin_manager.register(plugin)

    plugin_manager.load_setuptools_entrypoints("poodle")

    plugin_manager.register(get_poodle_config(), "poodle_config")


def collect_options():
    plugin_manager.hook.add_options(options=opt_collector)


def click_options_from_plugins():
    def decorator(f):
        for option in opt_collector.cli_options:
            click.option(*option["param_decls"], cls=option["cls"], **option["attrs"])(f)
        return f

    return decorator


def click_epilog_from_plugins():
    epilog = "\b\nConfiguration File Options:"
    epilog += (
        "\n  Options can be set in a configuration file.\n  See https://poodle.readthedocs.io/en/latest/options.html"
    )
    epilog += "\n\n"
    return epilog + opt_collector.click_epilog_from_plugins()
