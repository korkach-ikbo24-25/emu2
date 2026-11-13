"""Тесты функции to_dot (этап 5)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from visualize import to_dot


def test_empty_graph():
    """Пустой граф должен давать валидный DOT с корнем."""
    dot = to_dot({}, [], "A")
    assert "digraph deps {" in dot
    assert '"A"' in dot


def test_simple_edges():
    """Рёбра должны попасть в DOT."""
    edges = {"A": ["B", "C"], "B": [], "C": []}
    dot = to_dot(edges, [], "A")
    assert '"A" -> "B";' in dot
    assert '"A" -> "C";' in dot


def test_cycle_edges_are_red():
    """Обратные рёбра (циклы) должны быть красными."""
    edges = {"A": ["B"], "B": ["A"]}
    cycles = [("B", "A")]
    dot = to_dot(edges, cycles, "A")
    assert 'color="red"' in dot
    assert "dashed" in dot
