"""Тесты функции ascii_tree (этап 5)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from visualize import ascii_tree


def test_single_node():
    """Один узел без детей — только корень."""
    result = ascii_tree({"A": []}, "A")
    assert result == "A"


def test_linear_chain():
    """Цепочка A -> B -> C."""
    edges = {"A": ["B"], "B": ["C"], "C": []}
    result = ascii_tree(edges, "A")
    lines = result.splitlines()
    assert lines[0] == "A"
    assert "B" in lines[1]
    assert "C" in lines[2]


def test_cycle_does_not_hang():
    """Цикл должен помечаться и не зависать."""
    edges = {"A": ["B"], "B": ["A"]}
    result = ascii_tree(edges, "A")
    assert "(цикл)" in result
