from __future__ import annotations

import ast

from .config import PoodleConfigData
from .data import FileMutation


class MutatorBase:
    """Base class for Mutators."""

    mutator_name = ""

    def is_enabled(self, config: PoodleConfigData) -> bool:
        """Return True if mutator is enabled."""
        if self.mutator_name.lower() in config.skip_mutators:
            return False

        if config.only_mutators:
            return self.mutator_name.lower() in config.only_mutators

        return True

    def create_file_mutation(self, node: ast.AST, text: str) -> FileMutation:
        """Create a FileMutation copying location data from specified node."""
        lineno, col_offset, end_lineno, end_col_offset = self.get_location(node)

        return FileMutation(
            mutator_name=self.mutator_name,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
            text=text,
        )

    @staticmethod
    def get_location(node: ast.AST) -> tuple[int, int, int, int]:
        """Get location lines and columns that encompasses node and all child nodes."""
        lineno = node.lineno
        col_offset = node.col_offset
        end_lineno = node.end_lineno or node.lineno
        end_col_offset = node.end_col_offset or node.col_offset

        for n in ast.walk(node):
            if not hasattr(n, "lineno"):
                continue

            if n.lineno <= lineno:  # decorators
                lineno = n.lineno
                col_offset = min(n.col_offset, col_offset)

            if not hasattr(n, "end_lineno") or not n.end_lineno:
                continue

            if n.end_lineno > end_lineno:
                end_lineno = n.end_lineno
                end_col_offset = n.end_col_offset if n.end_col_offset else end_col_offset

            elif n.end_lineno == end_lineno and n.end_col_offset:
                end_col_offset = max(n.end_col_offset, end_col_offset)

        return (lineno, col_offset, end_lineno, end_col_offset)

    @classmethod
    def is_annotation(cls, node: ast.AST, child_node: ast.AST | None = None) -> bool:  # nomut: Keyword
        """Recursively search parent nodes to see if the starting node is part of an annotation.

        Returns true if a parent node points to this node in an annotation or returns attribute.
        """
        if not hasattr(node, "parent") or not node.parent:
            return False

        if hasattr(node, "annotation") and node.annotation == child_node:
            return True

        if hasattr(node, "returns") and node.returns == child_node:
            return True

        return cls.is_annotation(node.parent, child_node=node)

    @staticmethod
    def unparse_indent(node: ast.AST, indent: int) -> str:
        """Unparse AST node to string.  Indent any lines that are not the first line."""
        lines = ast.unparse(node).splitlines(keepends=True)
        lines[1:] = [f"{' ' * indent}{line}" for line in lines[1:]]
        return "".join(lines)
