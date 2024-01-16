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
    """Register Boolean Op Mutator Class."""
    plugin_manager.register(BooleanOpMutator(), "BooleanOpMutator")


class BooleanOpMutator(ast.NodeVisitor, MutatorBase):
    """Mutate Boolean Operators."""

    # https://docs.python.org/3/library/ast.html#ast.BoolOp
    # https://www.w3schools.com/python/python_operators.asp
    # ast.Or      or
    # ast.And     and

    type_map: ClassVar[dict[type, list[type]]] = {
        ast.Or: [ast.And],
        ast.And: [ast.Or],
    }

    mutator_name = "BoolOp"

    @hookimpl(specname="create_mutations")
    def create_mutations(self, parsed_ast: ast.Module, config: PoodleConfigData) -> list[FileMutation]:
        """Visit all Comparisons and return created mutants."""
        if not self.is_enabled(config):
            return []

        self.mutants = []
        self.visit(parsed_ast)
        return self.mutants

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Identify replacement Operations and create Mutants."""
        if self.is_annotation(node) or type(node.op) not in self.type_map:
            return

        for new_op in self.type_map[type(node.op)]:
            mut = deepcopy(node)
            mut.op = new_op()
            self.mutants.append(self.create_file_mutation(node, ast.unparse(mut)))
