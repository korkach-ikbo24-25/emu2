"""Модуль визуализации графа зависимостей."""
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Tuple


class VisualizeError(Exception):
    """Ошибка визуализации."""


def _format_edge(src: str, dst: str, is_cycle: bool) -> str:
    """Форматирует ребро графа в язык DOT."""
    if is_cycle:
        return f'  "{src}" -> "{dst}" [color="red", style="dashed"];'
    return f'  "{src}" -> "{dst}";'


def to_dot(
    edges: Dict[str, List[str]],
    cycles: List[Tuple[str, str]],
    root: str,
) -> str:
    """Генерирует текст на языке DOT."""
    lines = [
        "digraph deps {",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fillcolor="white"];',
    ]
    lines.append(f'  "{root}" [fillcolor="#cfe8ff"];')
    
    cycle_set = set(cycles)
    for src, dsts in edges.items():
        for dst in dsts:
            is_cycle = (src, dst) in cycle_set
            lines.append(_format_edge(src, dst, is_cycle))
            
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_svg(dot_source: str, out_path: str) -> None:
    """Запускает системный dot и сохраняет SVG."""
    dot_bin = shutil.which("dot")
    if dot_bin is None:
        raise VisualizeError("Graphviz 'dot' не найден в PATH")

    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    fd, tmp_dot = tempfile.mkstemp(suffix=".dot", dir=out_dir)
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(dot_source)
            
        res = subprocess.run(
            [dot_bin, "-Tsvg", tmp_dot, "-o", out_path],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise VisualizeError(f"Graphviz ошибка: {res.stderr.strip()}")
        if not os.path.isfile(out_path):
            raise VisualizeError(f"Файл не создан: {out_path}")
    finally:
        try:
            os.unlink(tmp_dot)
        except OSError:
            pass


def _process_node(stack, node, prefix, path, children, idx):
    """Вспомогательная функция для ascii_tree (снижение сложности)."""
    child = children[idx]
    is_last = (idx == len(children) - 1)
    connector = "└── " if is_last else "├── "

    if child in path:
        line = f"{prefix}{connector}{child} (цикл)"
        stack.append((node, prefix, path, children, idx + 1, [line]))
        return

    line = f"{prefix}{connector}{child}"
    new_prefix = prefix + ("    " if is_last else "│   ")
    
    stack.append((node, prefix, path, children, idx + 1, [line]))
    stack.append((child, new_prefix, path | {child}, 
                  children, 0, []))
    stack[-1] = (child, new_prefix, path | {child}, 
                 children, 0, [line])


def ascii_tree(edges: Dict[str, List[str]], root: str) -> str:
    """Генерирует ASCII-дерево зависимостей."""
    out = [root]
    stack = [(root, "", frozenset({root}), edges.get(root, []), 0)]

    while stack:
        node, prefix, path, children, idx = stack.pop()
        if idx >= len(children):
            continue
        
        child = children[idx]
        is_last = (idx == len(children) - 1)
        connector = "└── " if is_last else "├── "

        if child in path:
            out.append(f"{prefix}{connector}{child} (цикл)")
            stack.append((node, prefix, path, children, idx + 1))
            continue

        out.append(f"{prefix}{connector}{child}")
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        stack.append((node, prefix, path, children, idx + 1))
        stack.append((child, new_prefix, path | {child}, 
                      edges.get(child, []), 0))

    return "\n".join(out)
