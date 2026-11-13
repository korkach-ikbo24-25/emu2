"""Модуль визуализации графа зависимостей (этап 5)."""

import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Tuple

# Константы (правило М1: убираем магические числа)
DOT_FILENAME_SUFFIX = ".dot"
SVG_EXTENSION = ".svg"
DOT_COMMAND = "dot"


class VisualizeError(Exception):
    """Ошибка визуализации (например, не найден Graphviz)."""


def to_dot(
    edges: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root: str,
) -> str:
    """Создает текстовое представление графа на языке DOT.

    Args:
        edges: Словарь связей графа (узел -> список детей).
        cycles: Список кортежей обратных ребер (циклов).
        root: Корневой узел графа.

    Returns:
        Строка с кодом DOT.
    """
    lines: List[str] = []
    lines.append("digraph deps {")
    lines.append("  rankdir=LR;")
    lines.append(
        '  node [shape=box, style="rounded,filled", fillcolor="white"];'
    )
    lines.append('  edge [color="#333333"];')
    lines.append(f'  "{root}" [fillcolor="#cfe8ff", penwidth=2];')

    cycle_set = set(cycles)
    for src, dsts in edges.items():
        for dst in dsts:
            if (src, dst) in cycle_set:
                lines.append(
                    f'  "{src}" -> "{dst}" '
                    f'[color="red", penwidth=2, style="dashed"];'
                )
            else:
                lines.append(f'  "{src}" -> "{dst}";')

    lines.append("}")
    return "\n".join(lines) + "\n"


def _run_dot(dot_bin: str, tmp_dot: str, out_path: str) -> None:
    """Вспомогательная функция для запуска Graphviz.

    Args:
        dot_bin: Путь к исполняемому файлу dot.
        tmp_dot: Путь к временному файлу .dot.
        out_path: Путь, куда сохранить SVG.

    Raises:
        VisualizeError: Если dot завершился с ошибкой.
    """
    result = subprocess.run(
        [dot_bin, "-Tsvg", tmp_dot, "-o", out_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip() or "без сообщения"
        raise VisualizeError(
            f"Graphviz завершился с кодом {result.returncode}: {error_msg}"
        )


def render_svg(dot_source: str, out_path: str) -> None:
    """Сохраняет изображение графа в формате SVG через Graphviz.

    Args:
        dot_source: Текст графа на языке DOT.
        out_path: Имя выходного файла (с расширением .svg).

    Raises:
        VisualizeError: Если Graphviz не установлен или упал.
    """
    dot_bin = shutil.which(DOT_COMMAND)
    if dot_bin is None:
        raise VisualizeError(
            "Graphviz 'dot' не найден в PATH. Установите Graphviz "
            "(winget install Graphviz.Graphviz / sudo apt install graphviz) "
            "и перезапустите терминал."
        )

    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    fd, tmp_dot = tempfile.mkstemp(
        suffix=DOT_FILENAME_SUFFIX, dir=out_dir
    )
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(dot_source)
        
        _run_dot(dot_bin, tmp_dot, out_path)

        if not os.path.isfile(out_path):
            raise VisualizeError(f"Graphviz не создал файл: {out_path}")
    finally:
        try:
            os.unlink(tmp_dot)
        except OSError:
            pass


def _format_ascii_node(
    node: str, prefix: str, is_last: bool, is_cycle: bool
) -> str:
    """Форматирует одну строку ASCII-дерева.

    Args:
        node: Имя узла.
        prefix: Отступ для текущего уровня.
        is_last: Является ли узел последним ребенком.
        is_cycle: Является ли узел циклом.

    Returns:
        Отформатированная строка.
    """
    connector = "└── " if is_last else "├── "
    cycle_marker = " (цикл)" if is_cycle else ""
    return f"{prefix}{connector}{node}{cycle_marker}"


def ascii_tree(edges: Dict[str, List[str]], root: str) -> str:
    """Строит ASCII-дерево зависимостей от корня.

    Args:
        edges: Словарь связей графа (узел -> список детей).
        root: Корневой узел.

    Returns:
        Строка с деревом.
    """
    out: List[str] = [root]
    stack = [(root, "", frozenset({root}), edges.get(root, []), 0)]

    while stack:
        node, prefix, path, children, idx = stack.pop()
        if idx >= len(children):
            continue

        child = children[idx]
        is_last = (idx == len(children) - 1)
        is_cycle = child in path

        out.append(_format_ascii_node(child, prefix, is_last, is_cycle))

        stack.append((node, prefix, path, children, idx + 1))

        if not is_cycle:
            new_prefix = prefix + ("    " if is_last else "│   ")
            stack.append(
                (child, new_prefix, path | {child}, edges.get(child, []), 0)
            )

    return "\n".join(out)
