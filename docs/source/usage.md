# Usage & Configuration

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
Usage: poodle [OPTIONS] [SOURCE]...

  Poodle Mutation Test Tool.

Options:
  -C, --config_file PATH     Configuration File.
  -q                         Quiet mode: disabled normal output, and loglevel=ERROR
  -v                         Verbose mode: loglevel=INFO
  -vv                        Very Verbose mode: loglevel=DEBUG
  -P, --max_workers INTEGER  Maximum number of parallel workers.
  --exclude TEXT             Add a regex filter for which files NOT to mutate.  Multiple allowed.
  --only TEXT                Glob pattern for files to mutate.  If specified, no other files will be mutated.  Multiple allowed.
  --help                     Show this message and exit.
```

### SOURCE

Running each Trial consists of 3 steps:

1. Copy contents of a source folder to a temporary location.
2. Apply a single mutation to the copy of the source file.
3. Run test suite with the temporary folder added to the python path.

The list of Source folders is the root folder of a python project that should be copied to a temporary location.

Typically, this is a folder like 'src' or 'lib'.  But could be almost anything depending on your project structure.  

It should be the folder that contains your top level modules and/or packages.  It should not be the package folder itself.

If the python files are in the working folder, specify this as '.'

More than one can be specified.

**Default:** src, lib
:::{note}
Any folders specified in command line or in config files must exist.  If none is specified, it will use 'src' and/or 'lib' if they exist.
:::

Example: passing two folders, 'src' and 'build'
```bash
poodle src build
```

### config_file

By default, poodle will search the current working directory for 'poodle.toml' and 'pyproject.toml'.

the config_file option is used to specify an alternate config file.

Do not use config_file for specifying location of poodle_config.py

Accepted formats: toml

### Quiet Mode



## poodle_config.py

## poodle.toml

## pyproject.toml

## All Options