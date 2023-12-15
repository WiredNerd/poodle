"""Mutate Operators."""

from __future__ import annotations

import ast
from typing import Callable, ClassVar

from poodle.data_types import FileMutation, Mutator, PoodleConfig


class OperationMutator(ast.NodeVisitor, Mutator):
    """Base class for mutating operations."""

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

    type_map_levels: ClassVar[dict[str, dict[type, list[type]]]] = {
        "min": {
            ast.Add: [ast.Mult],
            ast.Sub: [ast.Div],
            ast.Mult: [ast.Add],
            ast.Div: [ast.Sub],
            ast.FloorDiv: [ast.Div],
            ast.Mod: [ast.Sub],
            ast.Pow: [ast.Mult],
            ast.LShift: [ast.RShift],
            ast.RShift: [ast.LShift],
            ast.BitOr: [ast.BitAnd],
            ast.BitXor: [ast.BitOr],
            ast.BitAnd: [ast.BitXor],
        },
        "std": {
            ast.Add: [ast.Sub, ast.Mult],
            ast.Sub: [ast.Add, ast.Div],
            ast.Mult: [ast.Div, ast.Add],
            ast.Div: [ast.Mult, ast.Sub],
            ast.FloorDiv: [ast.Mult, ast.Div],
            ast.Mod: [ast.FloorDiv, ast.Sub],
            ast.Pow: [ast.Mult, ast.Div],
            ast.LShift: [ast.RShift],
            ast.RShift: [ast.LShift],
            ast.BitOr: [ast.BitAnd],
            ast.BitXor: [ast.BitOr, ast.BitAnd],
            ast.BitAnd: [ast.BitOr],
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

    def __init__(self, config: PoodleConfig, echo: Callable, *args, **kwargs) -> None:
        """Initialize and read settings."""
        super().__init__(config, echo, *args, **kwargs)
        self.mutants: list[FileMutation] = []

        level = self.config.mutator_opts.get("operator_level", "std")
        if level not in self.type_map_levels:
            echo(f"WARN: Invalid value operator_opts.operator_level={level}.  Using Default value 'std'")
            level = "std"

        self.type_map: dict[type, list[type]] = self.type_map_levels[level]

    def create_mutations(self, parsed_ast: ast.Module, *_, **__) -> list[FileMutation]:
        """Visit ast nodes and return created mutants."""
        self.mutants = []
        self.add_parent_attr(parsed_ast)
        self.visit(parsed_ast)
        return self.mutants


class BinaryOperationMutator(OperationMutator):
    """Mutate Binary Operations."""

    mutator_name = "BinOp"

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Identify replacement Operations and create Mutants."""
        if self.is_annotation(node):
            return

        if type(node.op) in self.type_map:
            mut_types = self.type_map[type(node.op)]
            self.mutants.extend([self.create_bin_op_mutant(node, new_type) for new_type in mut_types])

    def create_bin_op_mutant(self, node: ast.BinOp, new_type: type) -> FileMutation:
        """Create BinOp with replacement operation."""
        return self.create_file_mutation(node, ast.unparse(ast.BinOp(left=node.left, op=new_type(), right=node.right)))


class AugAssignMutator(OperationMutator):
    """Mutate Augmented Assignments."""

    mutator_name = "AugAssign"

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Identify replacement Operations and create Mutants."""
        self.mutants.append(self.create_assign_mutant(node))

        if type(node.op) in self.type_map:
            mut_types = self.type_map[type(node.op)]
            self.mutants.extend([self.create_aug_assign_mutant(node, new_type) for new_type in mut_types])

    def create_assign_mutant(self, node: ast.AugAssign) -> FileMutation:
        """Create Assign to replace AugAssign."""
        return self.create_file_mutation(
            node,
            ast.unparse(ast.Assign(lineno=node.lineno, targets=[node.target], value=node.value)),
        )

    def create_aug_assign_mutant(self, node: ast.AugAssign, new_type: type) -> FileMutation:
        """Create replacement AugAssign with alternate operation."""
        return self.create_file_mutation(
            node,
            ast.unparse(ast.AugAssign(target=node.target, op=new_type(), value=node.value)),
        )
