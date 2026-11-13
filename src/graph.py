"""Модуль построения графа зависимостей."""
from typing import Dict, List, Tuple

WHITE, GRAY, BLACK = 0, 1, 2


class GraphError(Exception):
    """Ошибка построения графа."""


def build_graph(
    repo: Dict[str, List[str]], root: str
) -> Tuple[Dict[str, List[str]], List[str], List[Tuple[str, str]]]:
    """Строит граф итеративным DFS."""
    if root not in repo:
        raise GraphError(f"Пакет '{root}' отсутствует в репозитории")

    color: Dict[str, int] = {}
    edges: Dict[str, List[str]] = {}
    order: List[str] = []
    cycles: List[Tuple[str, str]] = []

    color[root] = GRAY
    order.append(root)
    stack = [(root, iter(repo.get(root, [])))]

    while stack:
        node, it = stack[-1]
        try:
            nxt = next(it)
        except StopIteration:
            color[node] = BLACK
            stack.pop()
            continue

        if nxt not in repo:
            edges.setdefault(node, [])
            continue

        edges.setdefault(node, [])
        if nxt not in edges[node]:
            edges[node].append(nxt)

        col = color.get(nxt, WHITE)
        if col == WHITE:
            color[nxt] = GRAY
            order.append(nxt)
            stack.append((nxt, iter(repo.get(nxt, []))))
        elif col == GRAY:
            cycles.append((node, nxt))

    return edges, order, cycles
