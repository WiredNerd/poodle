# mutatest mutators 3.1.0

## visit_BinOp (x)
Replace with random other member of group:
Group: ast.Add, ast.Sub, ast.Div, ast.Mult, ast.Pow, ast.Mod, ast.FloorDiv
Group: BitAnd, BitOr, BitXor
Group: LShift, RShift

## visit_AugAssign
Ignore if op is not Add,Sub,Mult,Div
Randomly replaces with different type of AugAssign +=, -=, *=, /+

## visit_Compare
Replace with random other member of group:
Group: ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE
Group: ast.Is, ast.IsNot
Group: ast.In, ast.NotIn

Logic about cases where there would be multiple ops?

## visit_Constant (mixin_NameConstant)
Replace with random other member of group:
Group True, False, None
Ignore other types

## visit_BoolOp
Replace with random other member of group:
Group: ast.And, ast.Or

## visit_If
Replace 
If True changes to If False
If False changes to If True
All other If statements not mutated

# visit_Subscript
Group (no lower bound), (no upper bound), (unbounded)
Ignore others

## visit_Index
Depreciated in 3.9, use index value instead
Replace with random other member of group:
Group: 0, positive (1), negative (-1)


