from typing import Dict, List, Set, Tuple


class GraphError(Exception):
    pass


def build_graph(
    repo: Dict[str, List[str]], root: str
) -> Tuple[Dict[str, List[str]], List[str], List[Tuple[str, str]]]:

    #   edges  — {узел: [дети]} (только рёбра, реально пройденные в графе)
    #   order  — порядок обнаружения узлов (полезно для отладки)
    #   cycles — список обратных рёбер (a, b): a -> b, где b уже в стеке

    if root not in repo:
        raise GraphError(f"Пакет '{root}' отсутствует в репозитории")

    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    edges: Dict[str, List[str]] = {}
    order: List[str] = []
    cycles: List[Tuple[str, str]] = []

    color[root] = GRAY
    order.append(root)
    # стек кадров: узел + итератор по его зависимостям
    stack: List[Tuple[str, "iter"]] = [(root, iter(repo.get(root, [])))]

    while stack:
        node, it = stack[-1]
        try:
            nxt = next(it)
        except StopIteration:
            color[node] = BLACK
            stack.pop()
            continue

        # зависимости, которых нет в индексе, считаем листьями
        if nxt not in repo:
            edges.setdefault(node, [])
            continue

        edges.setdefault(node, [])
        if nxt not in edges[node]:
            edges[node].append(nxt)

        c = color.get(nxt, WHITE)
        if c == WHITE:
            color[nxt] = GRAY
            order.append(nxt)
            stack.append((nxt, iter(repo.get(nxt, []))))
        elif c == GRAY:
            # обратное ребро — цикл; повторно не заходим
            cycles.append((node, nxt))
        # BLACK — узел уже полностью обработан, дубликат не нужен

    return edges, order, cycles
