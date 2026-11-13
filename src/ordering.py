"""Модуль вычисления порядка загрузки зависимостей."""
from typing import Dict, List, Tuple

WHITE, GRAY, BLACK = 0, 1, 2


def load_order(
    repo: Dict[str, List[str]], root: str
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Возвращает порядок загрузки и список циклов."""
    if root not in repo:
        raise ValueError(f"Пакет '{root}' отсутствует в репозитории")

    color: Dict[str, int] = {}
    order: List[str] = []
    cycles: List[Tuple[str, str]] = []

    color[root] = GRAY
    stack = [(root, iter(repo.get(root, [])))]

    while stack:
        node, it = stack[-1]
        try:
            nxt = next(it)
        except StopIteration:
            color[node] = BLACK
            order.append(node)
            stack.pop()
            continue

        if nxt not in repo:
            if color.get(nxt, WHITE) == WHITE:
                color[nxt] = BLACK
                order.append(nxt)
            continue

        col = color.get(nxt, WHITE)
        if col == WHITE:
            color[nxt] = GRAY
            stack.append((nxt, iter(repo.get(nxt, []))))
        elif col == GRAY:
            cycles.append((node, nxt))

    return order, cycles
