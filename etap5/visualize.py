import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Tuple


class VisualizeError(Exception):
    """Ошибка визуализации (например, не найден Graphviz)."""
    pass


def to_dot(
    edges: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root: str,
) -> str:
    """
    Текстовое представление графа на языке DOT.
    Корневой узел выделен заливкой, обратные рёбра (циклы) — красным.
    """
    lines: List[str] = []
    lines.append("digraph deps {")
    lines.append("  rankdir=LR;")
    lines.append('  node [shape=box, style="rounded,filled", fillcolor="white"];')
    lines.append('  edge [color="#333333"];')
    # корень — голубой
    lines.append(
        f'  "{root}" [fillcolor="#cfe8ff", penwidth=2];'
    )
    cycle_set = {(a, b) for a, b in cycles}
    for src, dsts in edges.items():
        for dst in dsts:
            if (src, dst) in cycle_set:
                # обратное ребро — красным и толще
                lines.append(
                    f'  "{src}" -> "{dst}" '
                    f'[color="red", penwidth=2, style="dashed"];'
                )
            else:
                lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_svg(dot_source: str, out_path: str) -> None:
    """
    Запускает системный `dot` (Graphviz) и пишет SVG в out_path.
    Бросает VisualizeError, если Graphviz не установлен или dot упал.
    """
    dot_bin = shutil.which("dot")
    if dot_bin is None:
        raise VisualizeError(
            "Graphviz 'dot' не найден в PATH. Установите Graphviz "
            "(winget install Graphviz.Graphviz / sudo apt install graphviz) "
            "и перезапустите терминал."
        )

    # временный .dot-файл рядом с целевым каталогом
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    fd, tmp_dot = tempfile.mkstemp(suffix=".dot", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(dot_source)
        result = subprocess.run(
            [dot_bin, "-Tsvg", tmp_dot, "-o", out_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise VisualizeError(
                f"Graphviz завершился с кодом {result.returncode}: "
                f"{result.stderr.strip() or 'без сообщения'}"
            )
        if not os.path.isfile(out_path):
            raise VisualizeError(
                f"Graphviz не создал файл: {out_path}"
            )
    finally:
        try:
            os.unlink(tmp_dot)
        except OSError:
            pass


def ascii_tree(
    edges: Dict[str, List[str]], root: str
) -> str:
    """
    ASCII-дерево зависимостей от root.
    Итеративно (без рекурсии), с защитой от циклов:
    повторно встреченный на текущем пути узел помечается '(цикл)'.
    """
    out: List[str] = [root]

    # кадр: (узел, префикс, путь-на-стеке, дети, индекс_следующего_ребёнка)
    stack: List[Tuple[str, str, frozenset, List[str], int]] = [
        (root, "", frozenset({root}), edges.get(root, []), 0)
    ]

    while stack:
        node, prefix, path, children, idx = stack.pop()
        if idx >= len(children):
            continue

        child = children[idx]
        is_last = (idx == len(children) - 1)
        connector = "└── " if is_last else "├── "

        if child in path:
            out.append(f"{prefix}{connector}{child} (цикл)")
            # не спускаемся; но продолжим перебирать остальных детей
            stack.append((node, prefix, path, children, idx + 1))
            continue

        out.append(f"{prefix}{connector}{child}")
        new_prefix = prefix + ("    " if is_last else "│   ")

        # сначала — «продолжение» текущего узла (следующий ребёнок),
        # потом — спуск в ребёнка (LIFO: спуск окажется «внутри»)
        stack.append((node, prefix, path, children, idx + 1))
        stack.append(
            (
                child,
                new_prefix,
                path | {child},
                edges.get(child, []),
                0,
            )
        )

    return "\n".join(out)
