# Poodle's Runners

```{code-block} text
:class: .no-copybutton
             .--~~,__                __            ,    /-.
:-....,-------`~~'._.'      \ ______/ V`-,        ((___/ __>
 `-,,,  ,_      ;'~U'        }        /~~         /      }
  _,-' ,'`-__; '--.         /_)^ --,r'            \ .--.(    ___
 (_/'~~      ''''(;        |b      |b              \\   \\  /___\
 ```

## Builtin Runner Names

* "command_line": [Command Line Runner](#command-line-runner)

## Command Line Runner

The command line runner runs the test suite by running the provided command in `subprocess.run`.

### Environment Variables:

The command line runner starts by copying the current environment variables, then making the following changes:
1. Add the temporary source folder to the beginning of "PYTHONPATH"
1. "PYTHONDONTWRITEBYTECODE": "1" - This tells python to skip compiling source code in this run.
1. "MUT_SOURCE_FILE": The name of the file that was mutated in this trial.
1. "MUT_LINENO": The start line of the mutation change.
1. "MUT_END_LINENO": The last line of the mutation change.
1. "MUT_COL_OFFSET": The first column of the MUT_LINENO that is being mutated.
1. "MUT_END_COL_OFFSET": The first column of the MUT_END_LINENO after the mutation change.
1. "MUT_TEXT": The text that was used to replace the above range in the source file.
1. Update environment variables with values from runner_opts.command_line_env (if any)

:::{note}
LINENO values start counting lines at 1.

COL_OFFSET values start counting columns at 0.

These values refer to the original source file, END values may not match mutated file.
:::

### Options:

#### command_line

Command to execute to test a trial.

Runner will replace the string `{PYTHONPATH}` in the command with the python path that includes the temporary running location.


**Default:** `"pytest -x --assert=plain -o pythonpath='{PYTHONPATH}'"`

:::{note}
Default includes options `-x` to stop execution at first failure, `--assert=plain` to skip extra processing when assertions fail, and `-o pythonpath='{PYTHONPATH}'` so that pytest doesn't add the current directory to the python path before running.
:::


::::{tab-set}

:::{tab-item} poodle_config.py
```python3
runner_opts = {
  "command_line":"pytest -x --assert=plain -o pythonpath= --sort-mode=fastest",
}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.runner_opts]
command_line = "pytest -x --assert=plain -o pythonpath= --sort-mode=fastest"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.runner_opts]
command_line = "pytest -x --assert=plain -o pythonpath= --sort-mode=fastest"
```
:::

::::

#### command_line_env

Use this to set additional environment variables in the subprocesses.

**Default:** `{}`

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
runner_opts = {
  "command_line_env":{"RUN_MODE":"MUTATION"},
}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.runner_opts.command_line_env]
RUN_MODE = "MUTATION"
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.runner_opts.command_line_env]
RUN_MODE = "MUTATION"
```
:::

::::
