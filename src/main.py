"""Точка входа CLI для инструмента depgraph."""

import os
import sys

# Добавляем src в путь импорта, чтобы найти соседние модули
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Константы кодов возврата (правило М1)
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 2
EXIT_REPO_ERROR = 3
EXIT_GRAPH_ERROR = 4

# Константы путей
DEFAULT_CONFIG_PATH = "data/config.csv"

from config_loader import Config, ConfigError, load_config
from graph import GraphError, build_graph
from ordering import load_order
from repo_apt import RepoError, load_repo_url
from repo_test import TestRepoError, load_test_repo
from visualize import VisualizeError, ascii_tree, render_svg, to_dot


def print_config(cfg: Config) -> None:
    """Выводит параметры конфигурации в формате ключ-значение."""
    print("=== Параметры конфигурации ===")
    print(f"  package    : {cfg.package}")
    print(f"  repo       : {cfg.repo}")
    print(f"  repo_mode  : {cfg.repo_mode}")
    print(f"  output     : {cfg.output}")
    print(f"  ascii_tree : {cfg.ascii_tree}")


def load_repo(cfg: Config):
    """Загружает репозиторий в зависимости от режима."""
    if cfg.repo_mode == "url":
        return load_repo_url(cfg.repo)
    return load_test_repo(cfg.repo)


def process_graph(cfg: Config, repo) -> None:
    """Строит граф, выводит порядок и визуализирует."""
    try:
        edges, order_nodes, cycles = build_graph(repo, cfg.package)
    except GraphError as e:
        print(f"[ОШИБКА ГРАФА] {e}", file=sys.stderr)
        sys.exit(EXIT_GRAPH_ERROR)

    total_edges = sum(len(v) for v in edges.values())
    print(f"\nУзлов в графе: {len(order_nodes)}")
    print(f"Рёбер в графе: {total_edges}")

    if cycles:
        print(f"Обнаружены циклы ({len(cycles)}):")
        for a, b in cycles:
            print(f"  {a} -> {b} (обратное ребро)")
    else:
        print("Циклов не обнаружено")

    print("\nРёбра графа:")
    for src in order_nodes:
        for dst in edges.get(src, []):
            print(f"  {src} -> {dst}")

    seq, _ = load_order(repo, cfg.package)
    print("\nПорядок загрузки (зависимости раньше пакета):")
    for i, p in enumerate(seq, 1):
        print(f"  {i:>2}. {p}")

    dot = to_dot(edges, cycles, cfg.package)
    try:
        render_svg(dot, cfg.output)
        print(f"\nSVG сохранён: {cfg.output}")
    except VisualizeError as e:
        print(f"[ОШИБКА ВИЗУАЛИЗАЦИИ] {e}", file=sys.stderr)

    if cfg.ascii_tree:
        print("\nASCII-дерево зависимостей:")
        print(ascii_tree(edges, cfg.package))


def main(argv: list[str]) -> int:
    """Главная функция приложения."""
    path = argv[1] if len(argv) > 1 else DEFAULT_CONFIG_PATH
    
    try:
        cfg = load_config(path)
    except ConfigError as e:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    print_config(cfg)

    try:
        repo = load_repo(cfg)
    except (RepoError, TestRepoError) as e:
        print(f"[ОШИБКА РЕПОЗИТОРИЯ] {e}", file=sys.stderr)
        return EXIT_REPO_ERROR

    process_graph(cfg, repo)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main(sys.argv))
