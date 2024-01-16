"""Mutate Comparison Operators."""

from __future__ import annotations

import ast
from copy import deepcopy
from typing import ClassVar

import pluggy

from poodle import FileMutation, MutatorBase, PoodleConfigData

hookimpl = pluggy.HookimplMarker("poodle")


@hookimpl(specname="register_plugins")
def register_plugins(plugin_manager: pluggy.PluginManager) -> None:
    """Register Comparison Mutator Class."""
    plugin_manager.register(ComparisonMutator(), "ComparisonMutator")


class ComparisonMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Comparison Operators."""

    # https://docs.python.org/3/library/ast.html#ast.Compare
    # https://www.w3schools.com/python/python_operators.asp
    # ast.Eq      ==
    # ast.NotEq   !=
    # ast.Lt      <
    # ast.LtE     <=
    # ast.Gt      >
    # ast.GtE     >=
    # ast.Is      is
    # ast.IsNot   is not
    # ast.In      in
    # ast.NotIn   not in

    type_map: ClassVar[dict[type, list[type]]] = {
        ast.Eq: [ast.NotEq],
        ast.NotEq: [ast.Eq],
        ast.Lt: [ast.GtE, ast.LtE],
        ast.LtE: [ast.Gt, ast.Lt],
        ast.Gt: [ast.LtE, ast.GtE],
        ast.GtE: [ast.Lt, ast.Gt],
        ast.Is: [ast.IsNot],
        ast.IsNot: [ast.Is],
        ast.In: [ast.NotIn],
        ast.NotIn: [ast.In],
    }

    mutator_name = "Compare"

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all Compare nodes and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_Compare(self, node: ast.Compare) -> None:
        """Identify replacement Operations and create Mutants."""

        for idx, op in enumerate(node.ops):
            for new_op in self.type_map[type(op)]:
                mut = deepcopy(node)
                mut.ops[idx] = new_op()
                self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))
