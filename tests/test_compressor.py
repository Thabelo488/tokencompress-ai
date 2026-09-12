"""Tests for code and prompt compression."""

import ast

from engine.ast_compressor import compress_python_code
from engine.knapsack_compressor import compress_prompt
from engine.token_counter import estimate_tokens


def test_ast_compression_preserves_valid_syntax_and_execution() -> None:
    source = '''"""module docs"""
# comment
VALUE = 3

def add(left, right):
    """function docs"""
    return left + right  # inline comment
'''
    compressed = compress_python_code(source)
    ast.parse(compressed)
    namespace = {}
    exec(compressed, namespace)
    assert namespace["add"](2, 4) == 6
    assert "module docs" not in compressed
    assert "function docs" not in compressed
    assert "#" not in compressed
    assert namespace["VALUE"] == 3


def test_ast_compression_returns_invalid_source_unchanged() -> None:
    source = "def broken(:\n"
    assert compress_python_code(source) == source


def test_knapsack_compression_respects_budget() -> None:
    source = (
        "Hello, please help me. "
        "The function must return an error for invalid input. "
        "Thank you for your assistance."
    )
    compressed = compress_prompt(source, max_tokens=12)
    assert estimate_tokens(compressed) <= 12
    assert "must return an error" in compressed


def test_knapsack_budget_and_empty_input_edges() -> None:
    assert compress_prompt("", 100) == ""
    assert compress_prompt("important return value", 0) == ""
    source = "Always return the requested class definition."
    assert compress_prompt(source, 100) == source


def test_structure_aware_selection_prefers_constraints_and_outputs() -> None:
    source = (
        "Hello, please provide a friendly explanation. "
        "Always validate input before processing. "
        "The output must return JSON. "
        "Thank you for your help."
    )
    compressed = compress_prompt(source, 18)
    assert "validate input" in compressed
    assert "return JSON" in compressed
    assert "Hello" not in compressed


def test_compression_avoids_redundant_units_and_stays_under_budget() -> None:
    source = (
        "Always validate the input before processing. "
        "Always validate the input before sending the request. "
        "Never expose credentials in logs. "
        "Return a JSON error for invalid input."
    )
    compressed = compress_prompt(source, 20)
    assert estimate_tokens(compressed) <= 20
    assert compressed.count("Always validate") <= 1
