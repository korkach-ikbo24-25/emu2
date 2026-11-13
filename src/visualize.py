# os — работа с путями и файлами
import os
# shutil — поиск исполняемого файла в PATH (which)
import shutil
# subprocess — запуск внешних программ (dot) из Python
import subprocess
# tempfile — временные файлы (.dot) для передачи в dot
import tempfile
# typing — подсказки типов
from typing import Dict, List, Tuple


# Собственное исключение для ошибок визуализации
class VisualizeError(Exception):
    # Докстринг
    """Ошибка визуализации (например, не найден Graphviz)."""
    # Пустое тело
    pass


# Публичная функция — DOT-представление графа
def to_dot(
    edges: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root: str,
) -> str:
    # Докстринг
    """
    Текстовое представление графа на языке DOT.
    Корень голубой, обратные рёбра — красные пунктирные.
    """
    # Будущие строки DOT
    lines: List[str] = []
    # Открываем digraph
    lines.append("digraph deps {")
    # Направление слева-направо
    lines.append("  rankdir=LR;")
    # Стиль узлов по умолчанию: скруглённый прямоугольник с белой заливкой
    lines.append('  node [shape=box, style="rounded,filled", fillcolor="white"];')
    # Цвет рёбер по умолчанию — тёмно-серый
    lines.append('  edge [color="#333333"];')
    # Корневой узел — с голубой заливкой и жирной рамкой
    lines.append(
        f'  "{root}" [fillcolor="#cfe8ff", penwidth=2];'
    )
    # Множество обратных рёбер — для быстрой проверки
    cycle_set = {(a, b) for a, b in cycles}
    # Идём по всем рёбрам
    for src, dsts in edges.items():
        # И по всем детям каждого узла
        for dst in dsts:
            # Если ребро — цикл
            if (src, dst) in cycle_set:
                # Рисуем красным пунктиром
                lines.append(
                    f'  "{src}" -> "{dst}" '
                    f'[color="red", penwidth=2, style="dashed"];'
                )
            # Иначе — обычное ребро
            else:
                # Стандартный стиль
                lines.append(f'  "{src}" -> "{dst}";')
    # Закрываем digraph
    lines.append("}")
    # Возвращаем текст с завершающим переводом строки
    return "\n".join(lines) + "\n"


# Публичная функция — рендер SVG через dot
def render_svg(dot_source: str, out_path: str) -> None:
    # Докстринг
    """
    Запускает системный `dot` (Graphviz) и пишет SVG в out_path.
    Бросает VisualizeError, если Graphviz не установлен или dot упал.
    """
    # Ищем dot в PATH
    dot_bin = shutil.which("dot")
    # Если не нашли — понятная ошибка с инструкцией
    if dot_bin is None:
        # Бросаем исключение
        raise VisualizeError(
            "Graphviz 'dot' не найден в PATH. Установите Graphviz "
            "(winget install Graphviz.Graphviz / sudo apt install graphviz) "
            "и перезапустите терминал."
        )

    # Абсолютный путь к выходному файлу
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    # Создаём временный .dot-файл в том же каталоге
    fd, tmp_dot = tempfile.mkstemp(suffix=".dot", dir=out_dir)
    # Оборачиваем в try/finally, чтобы точно удалить временный файл
    try:
        # Оборачиваем файловый дескриптор в объект-файл и пишем DOT
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # Записываем DOT-текст
            f.write(dot_source)
        # Запускаем dot; -Tsvg — выход SVG; -o — куда писать
        result = subprocess.run(
            [dot_bin, "-Tsvg", tmp_dot, "-o", out_path],
            capture_output=True,
            text=True,
        )
        # Если dot вернул ненулевой код — ошибка
        if result.returncode != 0:
            # Бросаем с stderr
            raise VisualizeError(
                f"Graphviz завершился с кодом {result.returncode}: "
                f"{result.stderr.strip() or 'без сообщения'}"
            )
        # Проверяем, что файл действительно создан
        if not os.path.isfile(out_path):
            # Иначе — ошибка
            raise VisualizeError(
                f"Graphviz не создал файл: {out_path}"
            )
    # finally выполнится даже при исключении
    finally:
        # Пытаемся удалить временный .dot
        try:
            # Удаляем файл
            os.unlink(tmp_dot)
        # Игнорируем ошибку удаления
        except OSError:
            # Ничего не делаем
            pass


# Публичная функция — ASCII-дерево зависимостей
def ascii_tree(
    edges: Dict[str, List[str]], root: str
) -> str:
    # Докстринг
    """
    ASCII-дерево зависимостей от root.
    Итеративно (без рекурсии), с защитой от циклов.
    """
    # Список строк результата, начинаем с корня
    out: List[str] = [root]

    # Стек кадров: (узел, префикс, путь-на-стеке, дети, индекс ребёнка)
    stack: List[Tuple[str, str, frozenset, List[str], int]] = [
        (root, "", frozenset({root}), edges.get(root, []), 0)
    ]

    # Основной цикл
    while stack:
        # Снимаем верхний кадр
        node, prefix, path, children, idx = stack.pop()
        # Если все дети обработаны — кадр больше не нужен
        if idx >= len(children):
            # Переходим к следующему кадру
            continue

        # Берём ребёнка по индексу
        child = children[idx]
        # Последний ли это ребёнок (для выбора └── vs ├──)
        is_last = (idx == len(children) - 1)
        # Символ-соединитель
        connector = "└── " if is_last else "├── "

        # Если ребёнок уже на текущем пути — цикл
        if child in path:
            # Печатаем с пометкой
            out.append(f"{prefix}{connector}{child} (цикл)")
            # Возвращаем кадр с увеличенным индексом
            stack.append((node, prefix, path, children, idx + 1))
            # Не спускаемся — иначе бесконечно
            continue

        # Печатаем ребёнка
        out.append(f"{prefix}{connector}{child}")
        # Новый префикс: вертикальная черта, если есть ещё дети, иначе пробелы
        new_prefix = prefix + ("    " if is_last else "│   ")

        # Сначала — «продолжение» текущего узла (следующий ребёнок)
        stack.append((node, prefix, path, children, idx + 1))
        # Затем — спуск в ребёнка (LIFO: он окажется «внутри»)
        stack.append(
            (
                # Ребёнок
                child,
                # Новый префикс
                new_prefix,
                # Путь + ребёнок (неизменяемое множество)
                path | {child},
                # Дети ребёнка
                edges.get(child, []),
                # Начинаем с первого
                0,
            )
        )

    # Склеиваем строки через перевод строки
    return "\n".join(out)
