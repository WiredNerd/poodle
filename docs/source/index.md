# Poodle
```{code-block} text
:class: .no-copybutton

    ____                  ____         ''',
   / __ \____  ____  ____/ / /__    o_)O \)____)"
  / /_/ / __ \/ __ \/ __  / / _ \    \_        )
 / ____/ /_/ / /_/ / /_/ / /  __/      '',,,,,,
/_/    \____/\____/\__,_/_/\___/         ||  ||
Poodle Mutation Tester                  "--'"--'
```

"A breed so perfect, so elegant, and so intelligent, that people decided to breed them with, well, everything." - [Girl With The Dogs](https://www.youtube.com/@GirlWithTheDogs)

[![PyPI - Version](https://img.shields.io/pypi/v/poodle)](https://pypi.org/project/poodle)
[![Homepage](https://img.shields.io/badge/Homepage-github-white)](https://github.com/WiredNerd/poodle)

Poodle is an tool for Mutation Testing your Python projects.

Mutation Testing proves the quality of your test suite by introducing bugs in your application, then verifying if your test cases can find the bug.

## Features

The goal of Poodle is to be highly efficient, configurable, and extendable.

* Multi-Threaded execution
* Highly Configurable
* Plug in custom code
* Output reports in Text, HTML, and JSON
* Python 3.9 - 3.12

## Quick Start

Installation:

```bash
pip install poodle --upgrade
```

```{code-block} text
:class: .no-copybutton

Usage: poodle [OPTIONS] [SOURCES]...

  Poodle Mutation Test Tool.

Options:
  -c PATH             Configuration File.
  -q                  Quiet mode: q, qq, or qqq
  -v                  Verbose mode: v, vv, or vvv
  -w INTEGER          Maximum number of parallel workers.
  --exclude TEXT      Add a glob exclude file filter. Multiple allowed.
  --only TEXT         Glob pattern for files to mutate. Multiple allowed.
  --report TEXT       Enable reporter by name. Multiple allowed.
  --html PATH         Folder name to store HTML report in.
  --json PATH         File to create with JSON report.
  --fail_under FLOAT  Fail if mutation score is under this value.
  --version           Show the version and exit.
  --help              Show this message and exit.
```

## Table of Contents
```{toctree}
:maxdepth: 1

mutation.md
usage.md
options.md
mutators.md
runners.md
reporters.md
credits.md
```

## Contribute

- Issue Tracker: https://github.com/WiredNerd/poodle/issues
- Source Code: https://github.com/WiredNerd/poodle

## Support

If you are having issues, please let us know.

I can be contacted at: pbuschmail-poodle@yahoo.com

Or by opening an issue: https://github.com/WiredNerd/poodle/issues

## License

The project is licensed under the MIT license.