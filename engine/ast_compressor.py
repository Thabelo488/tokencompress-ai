"""AST-based compression for Python source code."""

import ast
from typing import Optional


class DocumentationStripper(ast.NodeTransformer):
    """Remove documentation strings without changing executable statements."""

    def _strip_body_docstring(self, node: ast.AST) -> ast.AST:
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                body.pop(0)
        return node

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.generic_visit(node)
        return self._strip_body_docstring(node)  # type: ignore[return-value]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        return self._strip_body_docstring(node)  # type: ignore[return-value]

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        self.generic_visit(node)
        return self._strip_body_docstring(node)  # type: ignore[return-value]

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self.generic_visit(node)
        return self._strip_body_docstring(node)  # type: ignore[return-value]


def compress_python_code(source: str) -> str:
    """Strip docstrings and comments from valid Python, preserving syntax.

    Comments are not represented in Python's AST, so unparsing naturally removes
    them. If parsing fails, the original source is returned unchanged.
    """
    if not source.strip():
        return source
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError):
        return source

    cleaned_tree = DocumentationStripper().visit(tree)
    ast.fix_missing_locations(cleaned_tree)
    try:
        result = ast.unparse(cleaned_tree)
    except (AttributeError, ValueError):
        return source
    return result + ("\n" if result else "")
