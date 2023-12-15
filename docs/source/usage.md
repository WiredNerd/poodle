# Using Poodle

```text
            __                    __                     __
(\,--------'()'--o    (\,--------'()'--o     (\,--------'()'--o
 (_    ___    /~"      (_    ___    /~"       (_    ___    /~"
  (_)_)  (_)_)          (_)_)  (_)_)           (_)_)  (_)_)
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

## Getting Started

The most important thing is to tell poodle where your source code is.  By default, it will look for a folder named "src" or "lib".  But if the parent folder for your project is something else, you'll need to tell poodle where to look.

:::{tip}
In some systems it's necessary to prefix poodle command like: `python3 -m poodle`
:::

:::{dropdown} Project with "src" folder:
:open:

Example:
* src
  * main.py
  * util.py
  * query
    * \_\_init\_\_.py
    * database.py
* test
  * \_\_init\_\_.py
  * test_main.py
  * test_util.py
* pyproject.toml
* requirements.txt

Running with just `poodle` will find the folder.
:::

:::{dropdown} Project with "sources" folder:
Example:
* sources
  * main.py
  * util.py
  * query
    * \_\_init\_\_.py
    * database.py
* tests
  * \_\_init\_\_.py
  * test_main.py
  * test_util.py
* pyproject.toml
* requirements.txt

In this case, need to specify source folder like: `poodle sources`

DO NOT specify the package folders like "sources/query" as a source. Poodle needs the folder that contains the package folder.
:::

:::{dropdown} Project with multiple sources to mutate:
Example:
* application
  * main.py
  * query
    * \_\_init\_\_.py
    * database.py
* layer
  * util.py
* tests
  * \_\_init\_\_.py
  * test_main.py
  * test_util.py
* pyproject.toml
* requirements.txt

You can specify multiple folders to mutate like: `poodle application layer`

DO NOT specify the package folders like "application/query" as a source. Poodle needs the folder that contains the package folder.
:::

:::{dropdown} Flat project:
Example:
* query
  * \_\_init\_\_.py
  * database.py
* main.py
* pyproject.toml
* requirements.txt
* test_main.py
* test_util.py
* util.py

In this case, specify the source as the current folder: `poodle .`

DO NOT specify the package folders like "query" as a source
:::

:::{dropdown} Flat Package project:
Example:
* app
  * \_\_init\_\_.py
  * main.py
  * util.py
  * query
    * \_\_init\_\_.py
    * database.py
* test
  * \_\_init\_\_.py
  * test_main.py
  * test_util.py
* pyproject.toml
* requirements.txt

In this case, specify the source as the current folder: `poodle .`

DO NOT specify the package folders like "app" or "app/query" as a source. Poodle needs the folder that contains the package folder.
:::

### Configuration File

Poodle accepts several types of configuration files.

First is you can create `poodle_config.py` module. This is the most flexible option especially if you are adding custom code.

Second is a key/value config file like `pyproject.toml` or `poodle.toml`.  All options are listed in the [Options](options.md#configuration_file) page.

if you need to specify folders for your project, recommend putting that setting in your chosen config file with option [source_folders](options.md#source_folders)

### Start Small

If you have a lot of modules to scan, it can be helpful to start by scanning one or two at a time.  This can be accomplished with the `--only` flag.

```bash
poodle --only main.py --only database.py
```

## Whitelisting

Whitelisting is used to prevent mutations from being tested. This can be helpful in cases where mutation can't reasonably be tested. There are several methods to whitelist code in poodle.

### Line Comments

The best way to block a mutation on a specific line is to add a comment to the line.

:::{card}
```python3
x = y + 3  # nomut: Number
```
+++
This prevents only the "Number" mutator from mutating the statement.
:::

:::{card}
```python3
x = y + 3  # nomut: Number, BinOp
```
+++
This prevents only the "Number" and "BinOp" mutators from mutating the statement.
:::

:::{card}
```python3
x = y + 3  # nomut
```
or
```python3
x = y + 3  # nomut: all
```
or
```python3
x = y + 3  # pragma: no mutate
```
+++
This prevents all mutators from mutating the statement.
:::

:::{card}
```python3
x = y + 3  # nomut: start
x += 4
y *= 6  # nomut: end
```
or
```python3
x = y + 3  # nomut: on
x += 4
y *= 6  # nomut: off
```
+++
This prevents all mutators from mutating all three of these statements.
:::

### Whitelisting Entire Files

The best way to prevent mutation on an entire file is to add it to the [file_filters](options.md#file_filters) option in your configuration file.

### Disabling a Mutator

You can also disable a mutator completely using the [skip_mutators](options.md#skip_mutators) option in your configuration file.