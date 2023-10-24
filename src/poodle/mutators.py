from __future__ import annotations

import ast
from abc import ABC, abstractmethod

from poodle.data import FileMutant, PoodleConfig


class PoodleMutator(ABC):
    def __init__(self, config: PoodleConfig):
        self.config = config

    @abstractmethod
    def create_mutants(self, parsed_ast: ast.Module) -> list[FileMutant]:
        pass


class BinaryOperationMutator(ast.NodeVisitor, PoodleMutator):
    file_mutants: list[FileMutant]

    def create_mutants(self, parsed_ast: ast.Module) -> list[FileMutant]:
        self.file_mutants = []
        self.visit(parsed_ast)
        return self.file_mutants

    type_map = {
        ast.Add: [ast.Sub, ast.Mult],
        ast.Sub: [ast.Add, ast.Div],
        ast.Mult: [ast.Div, ast.Add],
        ast.Div: [ast.Mult, ast.Sub],
        ast.FloorDiv: ast.Div,
        ast.Mod: ast.FloorDiv,
        ast.Pow: ast.Mult,
        ast.LShift: ast.RShift,
        ast.RShift: ast.LShift,
        ast.BitOr: ast.BitXor,
        ast.BitXor: ast.BitOr,
        ast.BitAnd: ast.BitOr,
        # ast.MatMult:
    }

    def visit_BinOp(self, node: ast.BinOp):
        if type(node.op) in self.type_map:
            mut_types = self.type_map[type(node.op)]

            if not isinstance(mut_types, list):
                self.file_mutants.append(self.create_file_mutant(node, mut_types))
            else:
                self.file_mutants.extend([self.create_file_mutant(node, new_type) for new_type in mut_types])

    def create_file_mutant(self, node: ast.BinOp, new_type: type) -> FileMutant:
        return FileMutant(
            lineno=node.lineno,
            col_offset=node.col_offset,
            end_lineno=node.end_lineno,
            end_col_offset=node.end_col_offset,
            text=ast.unparse(ast.BinOp(left=node.left, op=new_type(), right=node.right)),
        )
