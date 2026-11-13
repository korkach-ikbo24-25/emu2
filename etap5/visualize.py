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
