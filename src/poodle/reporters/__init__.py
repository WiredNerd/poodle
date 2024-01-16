"""Report Mutation Testing Results."""

from . import reporter_html, reporter_json, reporter_sysout

reporter_plugins = [reporter_html, reporter_json, reporter_sysout]