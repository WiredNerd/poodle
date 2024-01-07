# Configuration Options

```{code-block} text
:class: .no-copybutton

              /\___/\              ,'.-.'.           .-"-.
              `)9 9('              '\~ o/`          /|6 6|\
              {_:Y:.}_              { @ }          {/(_0_)\}
--------------( )U-'( )----------oOo-----oOo------oOo--U--oO--------------------
____|_______|_______|_______|_______|_______|_______|_______|_______|_______|___
```

## Configuration Module

Poodle imports module `poodle_config.py`, if available, to set configuration options.

## Configuration File

Poodle will search for available configuration files, and use the first available file from this list:

1. poodle.toml
2. pyproject.toml

## Command Line

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

### Command Line Options

:::{list-table}
:header-rows: 0
:align: left

* - SOURCES 
  - [source_folders](#source_folders)
* - -c 
  - [config_file](#config_file)
* - -q 
  - [Quiet](#quiet-or-verbose)
* - -v 
  - [Verbose](#quiet-or-verbose)
* - -w 
  - [max_workers](#max_workers)
* - --exclude 
  - [file_filters](#file_filters)
* - --only 
  - [only_files](#only_files)
* - --report 
  - [report](#report)
* - --html 
  - [html](#html)
* - --json 
  - [json](#json)
* - --fail_under 
  - [fail_under](#fail_under)

:::

### Quiet or Verbose

The -q and -v flags control how quiet or verbose poodle will be.  These flags influence the values of [echo_enabled](#echo_enabled) and [log_level](#log_level).

:::{list-table}
:header-rows: 1
:align: left

* - Command Line
  - echo_enabled
  - log_level
* - `poodle -qqq`
  - `False`
  - `logging.CRITICAL`
* - `poodle -qq`
  - `False`
  - `logging.ERROR`
* - `poodle -q`
  - `False`
  - `logging.WARN`
* - `poodle` (default)
  - `True`
  - `logging.WARN`
* - `poodle -v`
  - `True`
  - `logging.INFO`
* - `poodle -vv`
  - `True`
  - `logging.DEBUG`
* - `poodle -vvv`
  - `True`
  - `logging.NOTSET`
:::

### Report

Add specified Reporter to the list of reporters to use.  This can be:
* Name of a [Builtin Reporter](reporters.md)
* String fully qualified name of the Mutator Class
* String fully qualified name of the Mutator Function

This option can be specified multiple times to add multiple reporters.  The reporters are added to the [reporters](#reporters) list

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --report=html --report=mypackage.myreporter
```
:::

::::

### HTML

Enable the HTML reporter and save the report to the specified folder.

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --html mutation-report/html
```
:::

::::

### JSON

Enable the JSON reporter and save the report to the specified file.

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --json mutation-report.json
```
:::

::::

## OPTIONS

Unless otherwise stated, options are chosen in this priority order:
1. Command Line options
2. Module poodle_config.py
3. Chosen Configuration File

### project_name

Name of project being tested.  Used by reporters to include the project name in the report.

If not specified, poodle will attempt to retrieve from project.name in pyproject.toml.

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
project_name = "myapp"
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
project_name = "myapp"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
project_name = "myapp"
```
:::

:::{tab-item} pyproject.toml
```toml
[project]
name = "myapp"
```
:::

::::

### project_version

Version of project being tested.  Used by reporters to include the project version in the report.

If not specified, poodle will attempt to retrieve from project.version in pyproject.toml.

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
project_version = "myapp"
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
project_version = "myapp"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
project_version = "myapp"
```
:::

:::{tab-item} pyproject.toml
```toml
[project]
version = "myapp"
```
:::

::::

### config_file

By default, Poodle will search for available configuration files, and use the first available file from this list:

1. poodle.toml
2. pyproject.toml

the config_file option is used to specify an alternate config file.

Do not use config_file for specifying location of poodle_config.py

Accepted formats: toml

::::{tab-set}

:::{tab-item} Command Line
poodle -c=config.toml
:::

:::{tab-item} poodle_config.py
```python3
config_file = "config.toml"
```
:::


::::

### source_folders

Folder(s) that contain your modules and/or packages.

**Default:** ["src", "lib"]

Running each Trial consists of 3 steps:

1. Copy contents of a source folder to a temporary location.
2. Apply a single mutation to the copy of the source file.
3. Run test suite with the temporary folder added to the python path.

The list of source folders is a root folder that should be copied to a temporary location.

Typically, this is a folder like 'src' or 'lib'.  But could be almost anything depending on your project structure.  

It should be the folder that contains your top level modules and/or packages.  It should not be the package folder itself.

If the python files are in the working folder, specify this as '.'

More than one can be specified.

:::{note}
Any folders specified in command line or in config files must exist.  If none is specified, it will use 'src' and/or 'lib' only if they exist.
:::

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle myapp myotherapp
```
:::

:::{tab-item} poodle_config.py
```python3
source_folders = ["myapp", "myotherapp"]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
source_folders = ["myapp", "myotherapp"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
source_folders = ["myapp", "myotherapp"]
```
:::

::::

### only_files

Only run mutation on files that match specified [GLOB](https://facelessuser.github.io/wcmatch/glob/) patterns.

When not specified, all python files that are in a [source_folder](#source_folders), and don't match a [file_filter](#file_filters) are mutated.

**Default:** `None`

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --only cli.py --only model_*.py
```
:::

:::{tab-item} poodle_config.py
```python3
only_files = ["cli.py", "model_*.py"]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
only_files = ["cli.py", "model_*.py"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
only_files = ["cli.py", "model_*.py"]
```
:::

::::

### file_filters

Files that match these filters will NOT be mutated.

Poodle uses glob matching from the [wcmatch](https://facelessuser.github.io/wcmatch/glob/) package for matching and filtering files.

**Default:** `["test_*.py", "*_test.py"]`

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --exclude sql_*.py --only text_*.py
```
:::

:::{tab-item} poodle_config.py
```python3
file_filters = ["sql_*.py", "text_*.py"]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
file_filters = ["sql_*.py", "text_*.py"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
file_filters = ["sql_*.py", "text_*.py"]
```
:::

::::

### file_flags

This option is to set the flags used when searching source folders for files to mutate, and applying exclude filters.  These flags are used either for searching with [only_files](#only_files) or with [file_filters](#file_filters).

Poodle uses glob matching from the [wcmatch](https://facelessuser.github.io/wcmatch/glob/) package for matching and filtering files.

**Default:** `wcmatch.glob.GLOBSTAR | wcmatch.glob.NODIR`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
from wcmatch import glob
file_flags = glob.GLOBSTAR | glob.NODIR | glob.DOTGLOB
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
file_flags = 16704
```

:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
file_flags = 16704
```
:::

::::

:::{tip}
Recommend setting this value in poodle_config.py only.  It must resolve to an `int` value. 

Setting this in toml has to be resolved int value of combining the flags.
:::

### file_copy_filters

Files that match these filters will NOT be copied to the temporary location.

Poodle uses glob matching from the [wcmatch](https://facelessuser.github.io/wcmatch/glob/) package for matching and filtering files.

**Default:** `["test_*.py", "*_test.py", "__pycache__/**"]`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
file_copy_filters = ["log.txt", "*.mdb"]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
file_copy_filters = ["log.txt", "*.mdb"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
file_copy_filters = ["log.txt", "*.mdb"]
```
:::

::::

### file_copy_flags

This option is to set the flags used when searching source folders for files copy to the temporary location.  These flags are used for searching with [file_copy_filters](#file_copy_filters).

Poodle uses glob matching from the [wcmatch](https://facelessuser.github.io/wcmatch/glob/) package for matching and filtering files.

**Default:** `wcmatch.glob.GLOBSTAR | wcmatch.glob.NODIR`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
from wcmatch import glob
file_copy_flags = glob.GLOBSTAR | glob.NODIR | glob.DOTGLOB
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
file_copy_flags = 16704
```

:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
file_copy_flags = 16704
```
:::

::::

:::{tip}
Recommend setting this value in poodle_config.py only.  It must resolve to an `int` value. 

Setting this in toml has to be resolved int value of combining the flags.
:::

### work_folder

Folder where temporary files will be stored.  Folder is deleted before and after execution.

**Default:** .poodle-temp

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
work_folder = "temp-files"
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
work_folder = "temp-files"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
work_folder = "temp-files"
```
:::

::::

### max_workers

By default, poodle sets the number of workers to be one less than the available CPUs from `os.sched_getaffinity` or `os.cpu_count`.  Use this option to manually set the number of workers.  With too few workers, available CPU is underutilized.  With too many workers, additional overhead of process switching slows execution.

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle -w 4
```
:::

:::{tab-item} poodle_config.py
```python3
max_workers = 4
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
max_workers = 4
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
max_workers = 4
```
:::

::::

### log_format

Logging Format for python's logging package.

**Default:** `"%(levelname)s [%(process)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
log_format = "%(levelname)s - %(message)s"
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
log_format = "%(levelname)s - %(message)s"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
log_format = "%(levelname)s - %(message)s"
```
:::

::::

### log_level

Logging Level for python's logging package.

**Default:** logging.WARN

::::{tab-set}

:::{tab-item} Command Line
```bash
python -v
```
See: [Quiet or Verbose](#quiet-or-verbose)
:::

:::{tab-item} poodle_config.py
```python3
log_level = logging.INFO
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
log_level = "INFO"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
log_level = "INFO"
```
:::

::::

### echo_enabled

This determines if Poodle's normal output should be enabled or not.

**Default:** `True`

::::{tab-set}

:::{tab-item} Command Line
```bash
python -q
```
See: [Quiet or Verbose](#quiet-or-verbose)
:::

:::{tab-item} poodle_config.py
```python3
echo_enabled = False
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
echo_enabled = "False"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
echo_enabled = "False"
```
:::

::::

### add_mutators

Additional mutators to be used when creating mutations.  This list can contain any of the following:
* Reference to the Mutator Class type
* Reference to the Mutator Function
* String fully qualified name of the Mutator Class
* String fully qualified name of the Mutator Function

**Default:** `[]`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
from poodle import Mutator

class CustomMutator(Mutator):
  ...

def other_mutator(config, echo, parsed_ast, *_, *__,):
  ...

add_mutators = [
    CustomMutator,
    other_mutator,
    "poodle-ext.mutators.SpecialObjectMutator",
    "poodle-ext.mutators.my_object_mutator",
]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
add_mutators = [
    "poodle-ext.mutators.SpecialObjectMutator",
    "poodle-ext.mutators.my_object_mutator",
]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
add_mutators = [
    "poodle-ext.mutators.SpecialObjectMutator",
    "poodle-ext.mutators.my_object_mutator",
]
```
:::

::::

### skip_mutators

Disables selected builtin mutators.  Specify the name of the mutator.  See [Poodle's Mutators](mutators.md)

**Default:** `[]`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
skip_mutators = ["FuncCall","DictArray"]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
skip_mutators = ["FuncCall","DictArray"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
skip_mutators = ["FuncCall","DictArray"]
```
:::

::::

### mutator_opts

This dict contains options that are used by various mutators.  Options for builtin mutators are listed below, and detailed on the Mutator page.

**Default:** `{}`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
mutator_opts = {"operator_level":"min"}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.mutator_opts]
operator_level = "min"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.mutator_opts]
operator_level = "min"
```
:::

::::

#### Builtin mutator_opts

Comparison Mutator:
* [compare_filters](mutators.md#comparison-mutator)

Operation Mutator:
* [operator_level](mutators.md#operator_level)

### runner

Indicates which trial runner to use.  Can be any of the following:
* Name of a builtin Runner Function
* Reference to the Runner Function
* String fully qualified name of the Runner Function

**Default:** "command_line"

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
def my_runner(config, echo, run_folder, mutant, timeout, *_, *__,):
  ...

runner = my_runner
```
:::

:::{tab-item} poodle_config.py
```python3
runner = "poodle-ext.runners.cool_runner"
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
runner = "poodle-ext.runners.cool_runner"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
runner = "poodle-ext.runners.cool_runner"
```
:::

::::

### runner_opts

This dict contains options that are used by various runners.  Options for builtin runners are listed below, and detailed on the Runner page.

**Default:** `{}`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
runner_opts = {
  "command_line":"pytest -x --assert=plain -o pythonpath= --sort-mode=fastest",
  "command_line_env":{"RUN_MODE":"MUTATION"},
}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.runner_opts]
command_line = "pytest -x --assert=plain -o pythonpath= --sort-mode=fastest"

[poodle.runner_opts.command_line_env]
RUN_MODE = "MUTATION"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.runner_opts]
command_line = "pytest -x --assert=plain -o pythonpath= --sort-mode=fastest"

[tool.poodle.runner_opts.command_line_env]
RUN_MODE = "MUTATION"
```
:::

::::

#### Builtin runner_opts

Command Line Runner:
* [command_line](runners.md#command_line)
* [command_line_env](runners.md#command_line_env)

### min_timeout

**Default:** 10 (seconds)

Shortest timeout value, in seconds, that can be used in the runner.

Timeout value is calculated as longest run from clean run tests, multiplied by timeout_multiplier.

If this calculated value is smaller than min_timeout, min_timeout is used instead.

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
min_timeout = 15
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
min_timeout = 15
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
min_timeout = 15
```
:::

::::

### timeout_multiplier

Used to calculate timeout value to use in runner.  Timeout value is calculated as longest run from clean run tests, multiplied by timeout_multiplier.

**Default:** 10

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
timeout_multiplier = 2
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
timeout_multiplier = 2
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
timeout_multiplier = 2
```
:::

::::

### reporters

List of all mutators to be used after all trials are completed.  This list can contain any of the following:
* Name of a [Builtin Reporter](reporters.md)
* Reference to the Mutator Class type
* Reference to the Mutator Function
* String fully qualified name of the Mutator Class
* String fully qualified name of the Mutator Function

**Default:** `["summary", "not_found"]`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
def my_reporter(config, echo, testing_results, *_, **__):
   ...

reporters = [
    "summary",
    my_reporter,
    "poodle-ext.reporters.UploadToResultsServer",
    "poodle-ext.reporters.text_errors_file",
]
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
reporters = [
    "summary",
    "poodle-ext.reporters.UploadToResultsServer",
    "poodle-ext.reporters.text_errors_file",
]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
reporters = [
    "summary",
    "poodle-ext.reporters.UploadToResultsServer",
    "poodle-ext.reporters.text_errors_file",
]
```
:::

::::

### reporter_opts

This dict contains options that are used by various reporters.  Options for builtin reporters are listed below, and detailed on the Reporter page.

**Default:** `{}`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
reporter_opts = {"not_found_file":"mutants-not-found.txt"}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.reporter_opts]
not_found_file = "mutants-not-found.txt"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.reporter_opts]
not_found_file = "mutants-not-found.txt"
```
:::

::::

#### Builtin reporter_opts

Common:
* [project_name](#project_name)
* [project_version](#project_version)

Not Found Reporter:
* [not_found_file](reporters.md#not_found_file)

JSON Reporter:
* [json_include_summary](reporters.md#json_include_summary)
* [json_report_file](reporters.md#json_report_file)
* [json_report_found](reporters.md#json_report_found)
* [json_report_not_found](reporters.md#json_report_not_found)

HTML Reporter:
* [report_folder](reporters.md#report_folder)
* [include_found_trials_on_index](reporters.md#include_found_trials_on_index)
* [include_found_trials_with_source](reporters.md#include_found_trials_with_source)

### fail_under

This option specifies a Mutation Score Goal for the project.  If the Mutation Score for this run of testing is under the fail_under value, poodle will output a message and end with a Return Code of 1.

The fail_under value is expressed as a Percentage of Mutants found.  A value of `85.2` means that the goal is to find 85.2% of Mutants.

**Default:** `None`

::::{tab-set}

:::{tab-item} Command Line
```bash
poodle --fail_under 85.2
```
:::

:::{tab-item} poodle_config.py
```python3
fail_under = 85.2
```
:::

:::{tab-item} poodle.toml
```toml
[poodle]
fail_under = 85.2
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle]
fail_under = 85.2
```
:::

::::