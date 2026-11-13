# sys — доступ к argv и exit
import sys

# Загрузка/валидация конфигурации
from config_loader import Config, ConfigError, load_config
# Построение графа (этап 3)
from graph import GraphError, build_graph
# Порядок загрузки (этап 4)
from ordering import load_order
# Загрузка реального репозитория (этап 2)
from repo_apt import RepoError, load_repo_url
# Загрузка тестового репозитория (этап 3)
from repo_test import TestRepoError, load_test_repo
# Визуализация (этап 5)
from visualize import VisualizeError, ascii_tree, render_svg, to_dot


# Печать параметров конфигурации
def print_config(cfg: Config) -> None:
    # Заголовок
    print("=== Параметры конфигурации ===")
    # Имя пакета
    print(f"  package    : {cfg.package}")
    # Источник
    print(f"  repo       : {cfg.repo}")
    # Режим
    print(f"  repo_mode  : {cfg.repo_mode}")
    # Выходной SVG
    print(f"  output     : {cfg.output}")
    # ASCII-флаг
    print(f"  ascii_tree : {cfg.ascii_tree}")


# Единая точка загрузки репозитория в зависимости от режима
def load_repo(cfg: Config):
    # Режим url — реальный репозиторий
    if cfg.repo_mode == "url":
        # Возвращаем словарь
        return load_repo_url(cfg.repo)
    # Иначе — тестовый файл
    return load_test_repo(cfg.repo)


# Главная функция
def main(argv: list[str]) -> int:
    # Путь к конфигу: 1-й аргумент или config.csv
    path = argv[1] if len(argv) > 1 else "config.csv"
    # Пытаемся загрузить конфиг
    try:
        # Загружаем
        cfg = load_config(path)
    # Ловим ошибки конфигурации
    except ConfigError as e:
        # Сообщение в stderr
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        # Код 2 — ошибка конфигурации
        return 2

    # Печатаем параметры
    print_config(cfg)

    # Загружаем репозиторий (URL или файл)
    try:
        # Загружаем
        repo = load_repo(cfg)
    # Ловим ошибки репозитория обоих видов
    except (RepoError, TestRepoError) as e:
        # Сообщение в stderr
        print(f"[ОШИБКА РЕПОЗИТОРИЯ] {e}", file=sys.stderr)
        # Код 3 — ошибка репозитория
        return 3

    # Строим граф
    try:
        # Итеративный DFS
        edges, order_nodes, cycles = build_graph(repo, cfg.package)
    # Ловим ошибки графа
    except GraphError as e:
        # Сообщение в stderr
        print(f"[ОШИБКА ГРАФА] {e}", file=sys.stderr)
        # Код 4 — ошибка графа
        return 4

    # Считаем общее число рёбер
    total_edges = sum(len(v) for v in edges.values())
    # Печатаем число узлов
    print(f"\nУзлов в графе: {len(order_nodes)}")
    # Печатаем число рёбер
    print(f"Рёбер в графе: {total_edges}")

    # Если есть циклы — печатаем их
    if cycles:
        # Заголовок с количеством
        print(f"Обнаружены циклы ({len(cycles)}):")
        # Каждое ребро
        for a, b in cycles:
            # Печатаем
            print(f"  {a} -> {b} (обратное ребро)")
    # Иначе — сообщаем, что чисто
    else:
        # Сообщение
        print("Циклов не обнаружено")

    # Печатаем рёбра
    print("\nРёбра графа:")
    # По узлам в порядке обнаружения
    for src in order_nodes:
        # По детям
        for dst in edges.get(src, []):
            # Печатаем
            print(f"  {src} -> {dst}")

    # === Этап 4: порядок загрузки ===
    # Считаем порядок
    seq, _ = load_order(repo, cfg.package)
    # Заголовок
    print("\nПорядок загрузки (зависимости раньше пакета):")
    # Нумеруем с 1
    for i, p in enumerate(seq, 1):
        # Печатаем с выравниванием
        print(f"  {i:>2}. {p}")

    # === Этап 5: визуализация ===
    # Генерируем DOT
    dot = to_dot(edges, cycles, cfg.package)
    # Пытаемся отрендерить SVG
    try:
        # Запускаем dot
        render_svg(dot, cfg.output)
        # Сообщаем, что файл создан
        print(f"\nSVG сохранён: {cfg.output}")
    # Ловим ошибку визуализации (например, dot не установлен)
    except VisualizeError as e:
        # Предупреждение в stderr; код возврата остаётся 0
        print(f"[ОШИБКА ВИЗУАЛИЗАЦИИ] {e}", file=sys.stderr)

    # Если включён ASCII-режим — печатаем дерево
    if cfg.ascii_tree:
        # Заголовок
        print("\nASCII-дерево зависимостей:")
        # Печатаем дерево
        print(ascii_tree(edges, cfg.package))

    # Успех
    return 0


# Точка входа: при запуске файла напрямую
if __name__ == "__main__":
    # Запускаем main и возвращаем его код как код процесса
    sys.exit(main(sys.argv))
