[![Homepage](https://img.shields.io/badge/Homepage-github-white)](https://github.com/WiredNerd/poodle)
[![python>=3.9](https://img.shields.io/badge/python->=3.8-orange)](https://pypi.org/project/poodle)
[![PyPI - Version](https://img.shields.io/pypi/v/poodle)](https://pypi.org/project/poodle)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/poodle)](https://pypi.org/project/poodle)
[![PyPI - License](https://img.shields.io/pypi/l/poodle)](https://github.com/WiredNerd/poodle/blob/main/LICENSE)


[![Code Coverage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2FWiredNerd%2Fpoodle%2Fmain%2Fcode-coverage.json&query=%24.totals.percent_covered_display&suffix=%25&label=Code%20Coverage&color=teal)](https://pytest-cov.readthedocs.io)
[![Documentation Status](https://readthedocs.org/projects/poodle/badge/?version=latest)](https://poodle.readthedocs.io/)
<!-- [![Mutation Coverage](https://img.shields.io/badge/dynamic/xml?url=https%3A%2F%2Fraw.githubusercontent.com%2FWiredNerd%2Fpoodle%2Fmain%2Fmutation-testing-report.xml&query=round((%2F%2Ftestsuites%5B1%5D%2F%40tests%20-%20%2F%2Ftestsuites%5B1%5D%2F%40disabled%20-%20%2F%2Ftestsuites%5B1%5D%2F%40failures%20-%20%2F%2Ftestsuites%5B1%5D%2F%40errors)div(%2F%2Ftestsuites%5B1%5D%2F%40tests%20-%20%2F%2Ftestsuites%5B1%5D%2F%40disabled)*100)&suffix=%25&label=Mutation%20Coverage&color=orange)](https://mutmut.readthedocs.io/) --> 

[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Code Style: black](https://img.shields.io/badge/Code_Style-Black-black)](https://black.readthedocs.io)
[![Linter: ruff](https://img.shields.io/badge/Linter-ruff-purple)](https://beta.ruff.rs/docs/)
<!-- [![Snyk Security](https://img.shields.io/badge/Snyk%20Security-monitored-FF66FF)](https://snyk.io/) -->

# Poodle

Poodle is an tool for Mutation Testing your Python projects.

Mutation Testing proves the quality of your test suite by introducing bugs in your application, then verifying if your test cases can find the bug.

## Features

The goal of Poodle is to be highly efficient, configurable, and extendable.

* Multi-Threaded execution
* Highly Configurable (toml and py)
* Plug in custom code

## Quick Start

Installation:

```
pip install poodle --upgrade
```

```
Usage: poodle [OPTIONS] [SOURCES]...

  Poodle Mutation Test Tool.

Options:
  -c PATH         Configuration File.
  -q              Quiet mode: q, qq, or qq
  -v              Verbose mode: v, vv, or vvv
  -w INTEGER      Maximum number of parallel workers.
  --exclude TEXT  Add a regex exclude file filter. Multiple allowed.
  --only TEXT     Glob pattern for files to mutate. Multiple allowed.
  --help          Show this message and exit.
```

## Documentation:

- https://poodle.readthedocs.io/

## Contribute

- Issue Tracker: https://github.com/WiredNerd/poodle/issues
- Source Code: https://github.com/WiredNerd/poodle

## Support

If you are having issues, please let us know.

I can be contacted at: pbuschmail-poodle@yahoo.com

Or by opening an issue: https://github.com/WiredNerd/poodle/issues

## License

The project is licensed under the MIT license.