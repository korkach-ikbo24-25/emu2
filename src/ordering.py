# typing — подсказки типов
from typing import Dict, List, Tuple


# Публичная функция — порядок загрузки (пост-обход DFS)
def load_order(
    repo: Dict[str, List[str]], root: str
) -> Tuple[List[str], List[Tuple[str, str]]]:
    # Докстринг
    """
    Возвращает (order, cycles): зависимости раньше пакета.
    Итеративный пост-обход DFS.
    """
    # Корень должен быть в репозитории
    if root not in repo:
        # Иначе — ValueError (вызывающий уже должен был проверить)
        raise ValueError(f"Пакет '{root}' отсутствует в репозитории")

    # Константы цветов
    WHITE, GRAY, BLACK = 0, 1, 2
    # Словарь цветов
    color: Dict[str, int] = {}
    # Итоговый порядок (пост-обход)
    order: List[str] = []
    # Список обратных рёбер
    cycles: List[Tuple[str, str]] = []

    # Корень — серый
    color[root] = GRAY
    # Стек кадров
    stack: List[Tuple[str, "iter"]] = [(root, iter(repo.get(root, [])))]

    # Основной цикл
    while stack:
        # Верхний кадр
        node, it = stack[-1]
        # Пытаемся взять ребёнка
        try:
            # next() бросает StopIteration при исчерпании
            nxt = next(it)
        # Дети кончились
        except StopIteration:
            # Помечаем чёрным
            color[node] = BLACK
            # Добавляем в порядок — пост-обход: после всех детей
            order.append(node)
            # Снимаем кадр
            stack.pop()
            # Следующая итерация
            continue

        # Зависимость не описана в индексе — считаем листом
        if nxt not in repo:
            # Если ещё не в порядке — добавляем
            if color.get(nxt, WHITE) == WHITE:
                # Помечаем чёрным
                color[nxt] = BLACK
                # Добавляем в порядок
                order.append(nxt)
            # Не создаём кадр
            continue

        # Смотрим цвет ребёнка
        c = color.get(nxt, WHITE)
        # Белый — спускаемся
        if c == WHITE:
            # Помечаем серым
            color[nxt] = GRAY
            # Пушим кадр
            stack.append((nxt, iter(repo.get(nxt, []))))
        # Серый — цикл
        elif c == GRAY:
            # Фиксируем обратное ребро
            cycles.append((node, nxt))
        # BLACK — уже в порядке, ничего не делаем

    # Возвращаем порядок и циклы
    return order, cycles
