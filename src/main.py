"""Точка входа CLI-приложения depgraph."""
import sys
import os

# Добавляем папку src в sys.path для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import Config, ConfigError, load_config
from graph import GraphError, build_graph
from ordering import load_order
from repo_apt import RepoError, load_repo_url
from repo_test import TestRepoError, load_test_repo
from visualize import VisualizeError, ascii_tree, render_svg, to_dot

EXIT_CONFIG = 2
EXIT_REPO = 3
EXIT_GRAPH = 4


def print_config(cfg: Config) -> None:
    """Выводит параметры конфигурации."""
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


def print_graph_summary(edges, nodes, cycles) -> None:
    """Выводит сводку по графу и циклы."""
    total_edges = sum(len(v) for v in edges.values())
    print(f"\nУзлов в графе: {len(nodes)}")
    print(f"Рёбер в графе: {total_edges}")

    if cycles:
        print(f"Обнаружены циклы ({len(cycles)}):")
        for a, b in cycles:
            print(f"  {a} -> {b} (обратное ребро)")
    else:
        print("Циклов не обнаружено")

    print("\nРёбра графа:")
    for src in nodes:
        for dst in edges.get(src, []):
            print(f"  {src} -> {dst}")


def print_load_order(repo, package) -> None:
    """Выводит порядок загрузки."""
    seq, _ = load_order(repo, package)
    print("\nПорядок загрузки (зависимости раньше пакета):")
    for i, pkg in enumerate(seq, 1):
        print(f"  {i:>2}. {pkg}")


def main(argv: list[str]) -> int:
    """Точка входа программы."""
    path = argv[1] if len(argv) > 1 else "data/config.csv"
    
    try:
        cfg = load_config(path)
    except ConfigError as err:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {err}", file=sys.stderr)
        return EXIT_CONFIG

    print_config(cfg)

    try:
        repo = load_repo(cfg)
    except (RepoError, TestRepoError) as err:
        print(f"[ОШИБКА РЕПОЗИТОРИЯ] {err}", file=sys.stderr)
        return EXIT_REPO

    try:
        edges, nodes, cycles = build_graph(repo, cfg.package)
    except GraphError as err:
        print(f"[ОШИБКА ГРАФА] {err}", file=sys.stderr)
        return EXIT_GRAPH

    print_graph_summary(edges, nodes, cycles)
    print_load_order(repo, cfg.package)

    dot = to_dot(edges, cycles, cfg.package)
    try:
        render_svg(dot, cfg.output)
        print(f"\nSVG сохранён: {cfg.output}")
    except VisualizeError as err:
        print(f"[ОШИБКА ВИЗУАЛИЗАЦИИ] {err}", file=sys.stderr)

    if cfg.ascii_tree:
        print("\nASCII-дерево зависимостей:")
        print(ascii_tree(edges, cfg.package))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
