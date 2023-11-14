"""Create Mutants."""

from __future__ import annotations

import ast
from typing import ClassVar

from click import echo

from poodle.data_types import FileMutation, Mutator, PoodleConfig


class BinaryOperationMutator(ast.NodeVisitor, Mutator):
    """Mutate Binary Operations."""

    # Binary Operators as of Python 3.12:
    # https://docs.python.org/3/library/ast.html#ast.BinOp
    # https://www.w3schools.com/python/python_operators.asp
    # ast.Add       +
    # ast.Sub       -
    # ast.Mult      *
    # ast.Div       /
    # ast.FloorDiv  //
    # ast.Mod       %
    # ast.Pow       **
    # ast.LShift    <<
    # ast.RShift    >>
    # ast.BitOr     |
    # ast.BitXor    ^
    # ast.BitAnd    &
    # ast.MatMult   @

    type_map_levels: ClassVar[dict[str, dict]] = {
        "min": {
            ast.Add: ast.Mult,
            ast.Sub: ast.Div,
            ast.Mult: ast.Add,
            ast.Div: ast.Sub,
            ast.FloorDiv: ast.Div,
            ast.Mod: ast.Sub,
            ast.Pow: ast.Mult,
            ast.LShift: ast.RShift,
            ast.RShift: ast.LShift,
            ast.BitOr: ast.BitAnd,
            ast.BitXor: ast.BitOr,
            ast.BitAnd: ast.BitXor,
        },
        "std": {
            ast.Add: [ast.Sub, ast.Mult],
            ast.Sub: [ast.Add, ast.Div],
            ast.Mult: [ast.Div, ast.Add],
            ast.Div: [ast.Mult, ast.Sub],
            ast.FloorDiv: [ast.Mult, ast.Div],
            ast.Mod: [ast.FloorDiv, ast.Sub],
            ast.Pow: [ast.Mult, ast.Div],
            ast.LShift: ast.RShift,
            ast.RShift: ast.LShift,
            ast.BitOr: [ast.BitAnd, ast.BitXor],
            ast.BitXor: [ast.BitOr, ast.BitAnd],
            ast.BitAnd: [ast.BitXor, ast.BitOr],
        },
        "max": {
            ast.Add: [ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow],
            ast.Sub: [ast.Add, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow],
            ast.Mult: [ast.Add, ast.Sub, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow],
            ast.Div: [ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod, ast.Pow],
            ast.FloorDiv: [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow],
            ast.Mod: [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Pow],
            ast.Pow: [ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod],
            ast.LShift: [ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd],
            ast.RShift: [ast.LShift, ast.BitOr, ast.BitXor, ast.BitAnd],
            ast.BitOr: [ast.LShift, ast.RShift, ast.BitXor, ast.BitAnd],
            ast.BitXor: [ast.LShift, ast.RShift, ast.BitOr, ast.BitAnd],
            ast.BitAnd: [ast.LShift, ast.RShift, ast.BitOr, ast.BitXor],
        },
    }

    def __init__(self, config: PoodleConfig, **_) -> None:
        """Initialize BinaryOperationMutator."""
        super().__init__(config)
        self.mutants: list[FileMutation] = []

        level = self.config.mutator_opts.get("bin_op_level", "std")
        if level not in self.type_map_levels:
            echo(f"WARN: Invalid value operator_opts.bin_op_level={level}.  Using Default value 'std'")  # TODO: Logging
            level = "std"

        self.type_map: dict = self.type_map_levels[level]

    def create_mutations(self, parsed_ast: ast.Module, **_) -> list[FileMutation]:
        """Visit all Binary Operations and return created mutants."""
        self.visit(parsed_ast)
        return self.mutants

    def visit_BinOp(self, node: ast.BinOp) -> None:  # noqa: N802
        """Identify replacement Operations and create Mutants."""
        if type(node.op) in self.type_map:
            mut_types = self.type_map[type(node.op)]

            if not isinstance(mut_types, list):
                self.mutants.append(self.create_mutant(node, mut_types))
            else:
                self.mutants.extend([self.create_mutant(node, new_type) for new_type in mut_types])

    def create_mutant(self, node: ast.BinOp, new_type: type) -> FileMutation:
        """Create Mutants."""
        return FileMutation(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno or node.lineno,
            end_col_offset=node.end_col_offset or node.col_offset,
            text=ast.unparse(ast.BinOp(left=node.left, op=new_type(), right=node.right)),
        )
