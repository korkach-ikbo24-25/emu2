from typing import Dict, List, Tuple


def load_order(
    repo: Dict[str, List[str]], root: str
) -> Tuple[List[str], List[Tuple[str, str]]]:
    # Возвращает (order, cycles):
    #   order  — порядок установки: зависимости раньше пакета
    #   cycles — список обратных рёбер (a, b): a -> b, где b уже в стеке
    # Итеративный пост-обход DFS (без рекурсии)
    # При наличии циклов строгий топопорядок невозможен
    # обратные рёбра фиксируются, обход не зацикливается
    if root not in repo:
        # сюда не должны попадать: build_graph уже проверил root
        raise ValueError(f"Пакет '{root}' отсутствует в репозитории")

    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    order: List[str] = []
    cycles: List[Tuple[str, str]] = []

    color[root] = GRAY
    stack: List[Tuple[str, "iter"]] = [(root, iter(repo.get(root, [])))]

    while stack:
        node, it = stack[-1]
        try:
            nxt = next(it)
        except StopIteration:
            # все дети обработаны значит фиксируем узел в порядке
            color[node] = BLACK
            order.append(node)
            stack.pop()
            continue

        if nxt not in repo:
            if color.get(nxt, WHITE) == WHITE:
                color[nxt] = BLACK
                order.append(nxt)
            continue

        c = color.get(nxt, WHITE)
        if c == WHITE:
            color[nxt] = GRAY
            stack.append((nxt, iter(repo.get(nxt, []))))
        elif c == GRAY:
            cycles.append((node, nxt))
        # BLACK — уже в порядке, ничего не делаем

    return order, cycles
