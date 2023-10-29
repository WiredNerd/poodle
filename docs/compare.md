# mutmut mutators 2.4.2

mutations_by_type = {
    'operator': dict(value=operator_mutation),
    'keyword': dict(value=keyword_mutation),
    'number': dict(value=number_mutation),
    'name': dict(value=name_mutation),
    'string': dict(value=string_mutation),
    'fstring': dict(children=fstring_mutation),
    'argument': dict(children=argument_mutation),
    'or_test': dict(children=and_or_test_mutation),
    'and_test': dict(children=and_or_test_mutation),
    'lambdef': dict(children=lambda_mutation),
    'expr_stmt': dict(children=expression_mutation),
    'decorator': dict(children=decorator_mutation),
    'annassign': dict(children=expression_mutation),
}

## operator_mutation
Ignore if it's an import statement (from name import *)
Ignore if value is * or ** and parent type is "param", 'argument', 'arglist'
Ignore if value is * and parent type is "parameters"

Replace: With
        '+': '-',
        '-': '+',
        '*': '/',
        '/': '*',
        '//': '/',
        '%': '/',
        '<<': '>>',
        '>>': '<<',
        '&': '|',
        '|': '&',
        '^': '&',
        '**': '*',
        '~': '',

        '+=': ['-=', '='],
        '-=': ['+=', '='],
        '*=': ['/=', '='],
        '/=': ['*=', '='],
        '//=': ['/=', '='],
        '%=': ['/=', '='],
        '<<=': ['>>=', '='],
        '>>=': ['<<=', '='],
        '&=': ['|=', '='],
        '|=': ['&=', '='],
        '^=': ['&=', '='],
        '**=': ['*=', '='],
        '~=': '=',

        '<': '<=',
        '<=': '<',
        '>': '>=',
        '>=': '>',
        '==': '!=',
        '!=': '==',
        '<>': '==',

## keyword_mutation
Ignore if context.stack[-2].type in ('comp_op', 'sync_comp_for') and value in ('in', 'is')
Ignore if context.stack[-2].type == 'for_stmt'

Replace: With
        'not': '',
        'is': 'is not',  # this will cause "is not not" sometimes, so there's a hack to fix that later
        'in': 'not in',
        'break': 'continue',
        'continue': 'break',
        'True': 'False',
        'False': 'True',

## number_mutation
https://docs.python.org/3/reference/lexical_analysis.html#integer-literals
Adds 1 to integers. 
Add 1 to floats between 1e-5 < abs(parsed) < 1e5 or parsed==0.0
    Else multiply by 2

## name_mutation
Replace: With
        'True': 'False',
        'False': 'True',
        'deepcopy': 'copy',
        'None': '""',

Replace Function Call with None
Replace array/dictionary lookup with None


## string_mutation
Ignore strings that are triple quoted 
"We assume here that triple-quoted stuff are docs or other things that mutation is meaningless for"

appears value always includes enclosing quotes
prefix is ' or "
mutation = prefix + value[0] + 'XX' + value[1:-1] + 'XX' + value[-1]

## fstring_mutation
Adds "XX" to the beginning and ending of the fString

## argument_mutation
Mutate the arguments one by one from dict(a=b) to dict(aXX=b)

## and_or_test_mutation
Replace: With
and: or
or: and

## lambda_mutation
If lambda simply returns None, instead return 0
Else change lambda to simply return None

## expression_mutation
If last value of expression is None, change to ""
else change last value to None

## decorator_mutation
Remove decorator

# mutatest mutators 3.1.0

## visit_AugAssign
Ignore if op is not Add,Sub,Mult,Div
Randomly replaces with different type of AugAssign +=, -=, *=, /+

## visit_BinOp
Replace with random other member of group:
Group: ast.Add, ast.Sub, ast.Div, ast.Mult, ast.Pow, ast.Mod, ast.FloorDiv
Group: BitAnd, BitOr, BitXor
Group: LShift, RShift

## visit_BoolOp
Replace with random other member of group:
Group: ast.And, ast.Or

## visit_Compare
Replace with random other member of group:
Group: ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE
Group: ast.Is, ast.IsNot
Group: ast.In, ast.NotIn

Logic about cases where there would be multiple ops?

## visit_If
If True changes to If False
If False changes to If True
All other If statements not mutated

## visit_Index
Depreciated, use index value instead
Replace with random other member of group:
Group: 0, positive (1), negative (-1)

## visit_Constant (mixin_NameConstant)
Replace with random other member of group:
Group True, False, None
Ignore other types

# visit_Subscript
Group (no lower bound), (no upper bound), (unbounded)
Ignore others

