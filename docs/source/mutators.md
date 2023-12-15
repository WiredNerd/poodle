# Poodle's Mutators

```text
    /''\,,,,,
   |    |    \           ___
    \   /  ^ |        __/_  `.  .-"""-.
   / \_/   0  \       \_,` | \-'  /   )`-')
  /            \       "") `"`    \  ((`"`
 /    ____      0     ___Y  ,    .'7 /|
/      /  \___ _/    (_,___/...-` (_/_/
```

:::{dropdown} "What do you call a labradoodle that can do Magic?"
"A Labra-cadabra-doodle"
:::

## Builtin Mutator Names

* "BinOp": [Binary Operation Mutator](#binary-operation-mutator)
* "AugAssign": [Augmented Assignment Mutator](#augmented-assignment-mutator)
* "UnaryOp": [Unary Operation Mutator](#unary-operation-mutator)
* "Compare": [Comparison Mutator](#comparison-mutator)
* "Keyword": [Keyword Mutator](#keyword-mutator)
* "Number": [Number Mutator](#number-mutator)
* "String": [String Mutator](#string-mutator)
* "FuncCall": [Function Call Mutator](#function-call-mutator)
* "DictArray": [Dict Array Call Mutator](#dict-array-call-mutator)
* "Lambda": [Lambda Return Mutator](#lambda-return-mutator)
* "Return": [Return Mutator](#return-mutator)
* "Decorator": [Decorator Mutator](#decorator-mutator)

## Binary Operation Mutator

**Name:** BinOp

Replaces operators used in binary expressions.  For example `x + y` becomes `x * y`

See [operator_level](#operator_level) for a list of all replacements included in this mutator.

If multiple operations are listed, the mutator will create multiple mutations for that location, one for each alternate operator.

## Augmented Assignment Mutator

**Name:** AugAssign

This mutator always creates multiple mutations for each location.  

First it creates a mutation changing the Augmented Assignment to Assignment.
* For example: `x += 3` becomes `x = 3`

Then it creates a mutation for each alternate operator in the [operator_level](#operator_level) mapping
* For example, `x += 3` becomes `x *= 3`

## Operation Mutator Options

There are two mutators that share the same operator mutation settings.  Both the [Binary Operation Mutator](#binary-operation-mutator) and [Augmented Assignment Mutator](#augmented-assignment-mutator) work by modifying the operator in the expression.  Both share the same [operator_level](#operator_level) option to determine how many replacements to use for each operator.

### operator_level

**Default:** "std"

**Allowed Values:** "min", "std", "max"

:::{list-table}
:header-rows: 1
:align: left

* - Operator
  - Symbol
  - "min"
  - "std"
  - "max"
* - Addition 
  - `+`
  - `*`
  - `-`, `*`
  - `-`, `*`, `/`, `//`, `%`, `**`
* - Subtraction 
  - `-`
  - `/`
  - `+`, `/`
  - `+`, `*`, `/`, `//`, `%`, `**`
* - Multiplication 
  - `*`
  - `+`
  - `/`, `+`
  - `+`, `-`, `/`, `//`, `%`, `**`
* - Division 
  - `/`
  - `-`
  - `*`, `-`
  - `+`, `-`, `*`, `//`, `%`, `**`
* - Floor Division 
  - `//`
  - `/`
  - `*`, `/`
  - `+`, `-`, `*`, `/`, `%`, `**`
* - Modulus 
  - `%`
  - `-`
  - `//`, `-`
  - `+`, `-`, `*`, `/`, `//`, `**`
* - Power 
  - `**`
  - `*`
  - `*`, `/`
  - `+`, `-`, `*`, `/`, `//`, `%`
* - Left Shift 
  - `<<`
  - `>>`
  - `>>`
  - `>>`, `|`, `^`, `&`
* - Right Shift 
  - `>>`
  - `<<`
  - `<<`
  - `<<`, `|`, `^`, `&`
* - Bitwise OR 
  - `|`
  - `&`
  - `&`
  - `<<`, `>>`, `^`, `&`
* - Bitwise XOR 
  - `^`
  - `|`
  - `|`, `&`
  - `<<`, `>>`, `|`, `&`
* - Bitwise AND 
  - `&`
  - `^`
  - `|`
  - `<<`, `>>`, `|`, `^`
* - Matrix Mult. 
  - `@`
  - N/A
  - N/A
  - N/A
:::

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

## Unary Operation Mutator

**Name:** UnaryOp

This mutator modifies unary operators Add, Subtract, Not, and Invert.

Examples:
* `x = +2` becomes `x = -2`
* `x = -2` becomes `x = +2`
* `if not x:` becomes `if x:`
* `x = ~2` becomes `x = 2`

## Comparison Mutator

**Name:** Compare

This mutator modifies comparison operators including some binary comparison operators.

However changing some comparisons can cause problems for testing tools, the mutator maintains a list of comparisons that should NOT be mutated.  In addition, compare_filters can be provided for additional patterns of comparisons that should not be mutated.  See [compare_filters](#compare_filters)

:::{list-table}
:header-rows: 1
:align: left

* - Operator
  - Symbol
  - Replacement(s)
* - Equality 
  - `==`
  - `!=`
* - Less Than 
  - `<`
  - `>=`, `<=`
* - Less Than or Equal
  - `<=`
  - `>`, `<`
* - Greater Than 
  - `>`
  - `<=`, `>=`
* - Greater Than or Equal
  - `>=`
  - `<`, `>`
* - is
  - `is`
  - `is not`
* - is not
  - `is not`
  - `is`
* - in
  - `in`
  - `not in`
* - not in
  - `not in`
  - `in`
* - or
  - `or`
  - `and`
* - and
  - `and`
  - `or`
:::

### Options

#### compare_filters

Additional [regex](https://docs.python.org/3/library/re.html) filters to prevent mutation of specific comparisons.

Default Filters:

* `r"__name__ == '__main__'"`

The default filters are always used, in addition to the ones specified in compare_filters.

::::{tab-set}

:::{tab-item} poodle_config.py
```python3
mutator_opts = {"compare_filters":[r"sys.version_info.minor\s*>\s*10"]}
```
:::

:::{tab-item} poodle.toml
```toml
[poodle.mutator_opts]
compare_filters = ["sys.version_info.minor\s*>\s*10"]
```
:::

:::{tab-item} pyproject.toml
```toml
[tool.poodle.mutator_opts]
compare_filters = ["sys.version_info.minor\s*>\s*10"]
```
:::

::::

:::{tip}
Modules are first parsed to [ast](https://docs.python.org/3/library/ast.html), then unparsed to text before comparing to the compare_filters.  For example, `__name__=="__main__"` is unparsed as `__name__ == '__main__'`

See how something is unparsed with a statement like:
```python3
import ast
ast.unparse(ast.parse('__name__=="__main__"',mode='eval'))
```
:::

## Keyword Mutator

**Name:** Keyword

This mutator modifies specific keywords:
* `break` becomes `continue`
* `continue` becomes `break`
* `True` becomes `False`
* `False` becomes `True`
* `None` becomes `' '`

## Number Mutator

**Name:** Number

This mutator modifies numbers that are hard coded in the code.  This can include int, octal int, hex int, binary int, float, complex.  Most numbers are mutated twice.

* `int` values are mutated as value + 1 and value - 1
* `complex` values are mutated as value + 1j and value - 1j
* `float` values are mutated as value / 2 and value * 2
  Unless the float == 0, then it's mutated to `1.0`

## String Mutator

**Name:** String

The string mutator adds "XX" to the beginning and end of strings.  It automatically skips docstrings.

## Function Call Mutator

**Name:** FuncCall

This mutator replaces calls to a function with the keyword `None`.

Examples:
* `my_func(123)` becomes `None`
* `x = my_func(123)` becomes `x = None`

## Dict Array Call Mutator

**Name:** DictArray

This mutator replaces calls to retrieve data from a dict or array/list object with `None`.

Examples:
* `abcd[1]` becomes `None`
* `abcd["efg"]` becomes `None`
* `x = abcd[1]` becomes `x = None`
* `x = abcd["efg"]` becomes `x = None`

## Lambda Return Mutator

**Name:** Lambda

This mutator changes the body of a lambda statement to return either `""` or `None`.

Examples:
* `lambda x,y: x+y` becomes `lambda x,y: None`
* `lambda z: None` becomes `lambda z: ""`

## Return Mutator

**Name:** Return

This mutator replaces the value being returned from a function with `""` or `None`.

Examples:
* `return 3` becomes `return None`
* `return my_variable` becomes `return None`
* `return None` becomes `return ""`

## Decorator Mutator

**Name:** Decorator

This mutator creates mutations where decorators are removed.

Example Input:
```python3
@log_input()
@cache
def my function(a,b):
    ...
```

Mutation 1:
```python3
@cache
def my function(a,b):
    ...
```

Mutation 2:
```python3
@log_input()
def my function(a,b):
    ...
```
