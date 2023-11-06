from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import Dict, List

from poodle.data import FileMutant, PoodleConfig

# import ast
# from poodle import PoodleConfig, FileMutant
# create_mutants(config: PoodleConfig, parsed_ast: ast.Module) -> List[FileMutant]:


class PoodleMutator(ABC):
    def __init__(self, config: PoodleConfig):
        self.config = config

    @abstractmethod
    def create_mutants(self, parsed_ast: ast.Module) -> List[FileMutant]:
        pass


class BinaryOperationMutator(ast.NodeVisitor, PoodleMutator):
    def __init__(self, config: PoodleConfig):
        super().__init__(config)
        self.file_mutants: List[FileMutant] = []

        level = self.config.mutator_opts.get("bin_op_level", "std")
        if level not in self.type_map_levels:
            print(f"WARN: Invalid value operator_opts.bin_op_level={level}.  Using Default value 'std'")
            level = "std"

        self.type_map: dict = self.type_map_levels[level]

    def create_mutants(self, parsed_ast: ast.Module) -> List[FileMutant]:
        self.visit(parsed_ast)
        return self.file_mutants

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
    # ast.MatMult   @ - Matrix Multiplication

    type_map_levels: Dict[str, dict] = {
        "min": {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.Div,
            ast.Div: ast.Mult,
            ast.FloorDiv: ast.Div,
            ast.Mod: ast.FloorDiv,
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
            ast.FloorDiv: ast.Div,
            ast.Mod: ast.FloorDiv,
            ast.Pow: ast.Mult,
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
