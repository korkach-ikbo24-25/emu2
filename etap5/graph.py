# typing — подсказки типов
from typing import Dict, List, Tuple


# Собственное исключение для ошибок графа
class GraphError(Exception):
    # Докстринг
    """Ошибка построения графа."""
    # Пустое тело
    pass


# Публичная функция — построение графа итеративным DFS
def build_graph(
    repo: Dict[str, List[str]], root: str
) -> Tuple[Dict[str, List[str]], List[str], List[Tuple[str, str]]]:
    # Докстринг
    """
    Итеративный DFS от root.
    Возвращает (edges, order, cycles).
    """
    # Корень должен быть в репозитории
    if root not in repo:
        # Иначе — ошибка
        raise GraphError(f"Пакет '{root}' отсутствует в репозитории")

    # Константы цветов для алгоритма DFS
    WHITE, GRAY, BLACK = 0, 1, 2
    # Словарь цветов: по умолчанию WHITE (отсутствие ключа = WHITE)
    color: Dict[str, int] = {}
    # Рёбра: {узел: [дети]}
    edges: Dict[str, List[str]] = {}
    # Порядок обнаружения узлов (для отладки/вывода)
    order: List[str] = []
    # Список обратных рёбер (циклов)
    cycles: List[Tuple[str, str]] = []

    # Корень сразу серый — в стеке
    color[root] = GRAY
    # Запоминаем порядок обнаружения
    order.append(root)
    # Стек кадров: (узел, итератор по его зависимостям)
    stack: List[Tuple[str, "iter"]] = [(root, iter(repo.get(root, [])))]

    # Основной цикл, пока стек не пуст
    while stack:
        # Берём верхний кадр, не снимая
        node, it = stack[-1]
        # Пытаемся взять следующего ребёнка
        try:
            # next() бросает StopIteration, если дети кончились
            nxt = next(it)
        # Дети кончились — завершаем узел
        except StopIteration:
            # Помечаем чёрным — полностью обработан
            color[node] = BLACK
            # Снимаем кадр со стека
            stack.pop()
            # Переходим к следующей итерации
            continue

        # Зависимость, которой нет в индексе, считаем листом
        if nxt not in repo:
            # Гарантируем, что у узла есть (возможно, пустой) список детей
            edges.setdefault(node, [])
            # Не создаём ребро — такого узла у нас нет
            continue

        # Гарантируем, что у узла есть список детей
        edges.setdefault(node, [])
        # Добавляем ребро, только если его ещё нет
        if nxt not in edges[node]:
            # Добавляем ребёнка
            edges[node].append(nxt)

        # Смотрим цвет ребёнка
        c = color.get(nxt, WHITE)
        # Белый — не посещали, спускаемся
        if c == WHITE:
            # Помечаем серым — в стеке
            color[nxt] = GRAY
            # Запоминаем в порядок
            order.append(nxt)
            # Пушим кадр для ребёнка
            stack.append((nxt, iter(repo.get(nxt, []))))
        # Серый — уже в стеке, значит обратное ребро (цикл)
        elif c == GRAY:
            # Фиксируем цикл
            cycles.append((node, nxt))
        # BLACK — уже обработан, повторно не спускаемся (ничего не делаем)

    # Возвращаем всё, что собрали
    return edges, order, cycles
