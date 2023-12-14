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

## Builtin Runner Names

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
  - `&`, `^`
  - `<<`, `>>`, `|`, `^`, `&`
* - Bitwise XOR 
  - `^`
  - `|`
  - `|`, `&`
  - `<<`, `>>`, `|`, `&`
* - Bitwise AND 
  - `&`
  - `^`
  - `^`, `|`
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

## Comparison Mutator

## Keyword Mutator

## Number Mutator

## String Mutator

## Function Call Mutator

## Dict Array Call Mutator

## Lambda Return Mutator

## Return Mutator

## Decorator Mutator
