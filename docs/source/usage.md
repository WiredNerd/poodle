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

* SOURCES [Source Folders](#source_folders)
* -c [Configuration File](#config_file)
* -q [Quiet Mode]()
* -v [Verbose Mode]()
* -w [Max Workers]()
* --exclude []()
* --only []()


### Quiet Mode

This option suppresses normal output, and set's log level to ERROR

### Verbose Mode

This set's log level to INFO

### max_workers

By default, poodle sets the number of workers to be one less than the available CPUs from `os.sched_getaffinity` or `os.cpu_count`.  Use this option to manually set the number of workers.  With too few workers, available CPU is underutilized.  With too many workers, additional overhead of process switching slows execution.

### exclude

This option excludes files that match the specified regex from the mutation processes.

Multiple allowed.

### only

This option restricts mutation to only the specified file

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
3. Chosen [Configuration File](#config_file)

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

### file_filters

### file_copy_filters

### work_folder

### max_workers

### log_format

### log_level

### echo_enabled

### mutator_opts

### skip_mutators

### add_mutators

### min_timeout

### timeout_multiplier

### runner

### runner_opts

### reporters

### reporter_opts
