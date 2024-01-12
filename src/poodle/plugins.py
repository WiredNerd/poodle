"""Manage Plugins."""

from __future__ import annotations

import click
import pluggy

from poodle.reporters import html, json, sysout

from .common import hook_spec
from .common.base import poodle_config

plugin_manager = pluggy.PluginManager("poodle")


def register_plugins():
    plugin_manager.add_hookspecs(hook_spec)

    plugin_manager.register(html.HtmlReporter())
    plugin_manager.register(json.JsonReporter())
    plugin_manager.register(sysout.SysoutReporter())

    plugin_manager.register(poodle_config)


def options_from_plugins():
    opt_collector = hook_spec.PoodleOptionCollector()
    plugin_manager.hook.add_options(options=opt_collector)

    def decorator(f):
        for option in opt_collector.cli_options:
            click.option(*option["param_decls"], cls=option["cls"], **option["attrs"])(f)
        return f

    return decorator
