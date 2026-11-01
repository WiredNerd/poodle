# Mutation Testing

```{code-block} text
:class: .no-copybutton
                                                             .-.
(___________________________________________________________()6 `-,
(   ______________________________________________________   /''"`
//\\                                                      //\\
"" ""                                                     "" ""
```

## Why Mutation Test?

Unit testing is used to ensure each unit of a program function as intended.  It can expose issues in code early in the development process.  The unit tests can also identify unintended impacts as other changes are made to the code in the future.  But how do you know if the unit test cases are adequate?

The first thing to use is a Code Coverage tool, like [coverage.py](https://coverage.readthedocs.io/).  Code Coverage monitors the testing to see which lines of code are executed.  It can help you find out if you hit every line of code and every branch.  However, this is a limited measure of the test suite.  Code Coverage tells you that the lines and branches were executed at least once, but it doesn't tell you if the test cases are really validating the logic of the code.  The solution for this is Mutation Testing.  

## What is Mutation Testing?

Mutation Testing is the process of introducing logical errors in the source code, then running the test suite. If the test suite reports an error, it was able to detect the mutation. In that case it confirms that the test suite is properly validating the logic that was modified. If the test suite doesn't report an error, then improvements are likely needed in the test suite's validations.

**Oversimplified Example:**
```{code-block} python3
:class: .no-copybutton
def my_func(a,b):
    return a + b

def test_my_func():
    assert my_func(2,2) == 4
```

This example by itself is not to be very realistic.  It's representative of the kinds of problems that can occur with much more complex pieces of code.

In this example, the test case passes, and code coverage shows 100%.  But did we really test the logic?  let's try it with a mutation.

Change `a + b` to `a * b`:

```{code-block} python3
:class: .no-copybutton
:emphasize-lines: 2
def my_func(a,b):
    return a * b

def test_my_func():
    assert my_func(2,2) == 4
```

The test case still passes.  That means the test case did not fully test the logic.  So, let's add some more assertions to test this better:

```{code-block} python3
:class: .no-copybutton
:emphasize-lines: 3,4
def test_my_func():
    assert my_func(2,2) == 4
    assert my_func(3,3) == 6
    assert my_func(1,3) == 4
```

Now, the test case passes with `a + b` and fails with `a * b`.  We can now confidently say that the test case is adequately testing the logic of the function.

## Why Poodle?

When I was looking for a Python Mutation Testing tool, the top candidates I found were [Mutmut](https://mutmut.readthedocs.io) and [Mutatest](https://mutatest.readthedocs.io/).  Both are good tools with pros and cons of each.  Poodle provides several advantages over these tools.  First is it runs multiple mutations in parallel, reducing runtime. It includes multiple methods of white-listing code, blocking mutations that can't be reasonably unit tested. It also highly configurable allowing testing to be customized to needs of the application. Finally it allows for custom code to be plugged in for further customization.

Mutmut mutates the source code, but it's done in place. Therefore it can only test one mutation at a time.  And there's a risk of mutations being left behind if the program ends abnormally.  Mutatest creates a copy of the python cache and applies the mutation to the cache.  This allows Mutatest to run in with parallel processing. But I've had problems in some environments with it creating too many parallel processes, resulting in frequent timeout errors. 

Poodle uses python's [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) package to enable testing multiple mutations in parallel. It copies the source code to a temporary location, applies a mutation, and then runs testing against that location. There is no risk of mutations being left in source code, since it's modifying a copy. Also less likely to break with future python versions, since it's not directly linked to the processes around maintaining python's cache. Finally, configuration options allow for manually limiting the parallel processing in cases where timeouts are occurring.

Poodle allows for configuration through command line, configuration text files, and python code. One of Poodle's goals is to provide reasonable defaults, so it can be used with minimal configuration.  But also to make as many configuration options available as possible.  That way the tool can be customized to as many different situations and needs as possible.

Poodle is also enables users to use custom code by creating a `poodle_config.py` module.  In this module, users can add custom mutator, runner, and reporter functions.  Poodle will pickup and use these in the testing cycle.
