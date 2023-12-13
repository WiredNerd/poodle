# Usage & Configuration

```text
              /\___/\              ,'.-.'.           .-"-.
              `)9 9('              '\~ o/`          /|6 6|\
              {_:Y:.}_              { @ }          {/(_0_)\}
--------------( )U-'( )----------oOo-----oOo------oOo--U--oO--------------------
____|_______|_______|_______|_______|_______|_______|_______|_______|_______|___
```



## Terminology

Mutation Testing can introduce some confusing language.  For example, we run the test suite and a test case failed.  In mutation testing, we want to testing to fail, so the test suite passed.  passed == failed?

So, in this application, I use the following terms whenever possible to help make things clearer

Mutation
: An intentional bug added to the code.  For example, changing `x + y` to `x - y`.

Trial
: A run of the entire test suite.  Usually to validate if the Test Suite can find the Mutation.

Passed
: When a Test Suite or Test Case ends without an error.

Failure
: When a Test Suite or Test Case ends with an error or non-successful return code.

Found
: If a Trial of a Mutation results in a Failure, then the Mutation was Found.

Not Found
: If a Trial of a Mutation results in a successful completion, then the Mutation was Not Found.

Timeout
: If the time to run a Trial exceeds a reasonable limit, the Trial is reported as Timeout instead of Found or Not Found.

Errors
: If a Trial results in an exception that is not normally expected from the Test Suite.

## Command Line

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

### Command Line Options

* SOURCES [source_folders](#source_folders)
* -c [config_file](#config_file)
* -q [Quiet](#quiet-or-verbose)
* -v [Verbose](#quiet-or-verbose)
* -w [max_workers](#max_workers)
* --exclude [file_filters](#file_filters)
* --only [only_files](#only_files)


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

## Configuration Module

Poodle imports module `poodle_config.py`, if available, to set configuration options.

## Configuration File

Poodle will search for available configuration files, and use the first available file from this list:

1. poodle.toml
2. pyproject.toml

## OPTIONS

Unless otherwise stated, options are chosen in this priority order:
1. Command Line options
2. Module poodle_config.py
3. Chosen Configuration File

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

### skip_mutators

### mutator_opts

### runner

### runner_opts

### min_timeout

### timeout_multiplier

### reporters

### reporter_opts
