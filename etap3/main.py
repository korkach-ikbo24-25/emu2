import sys

from config_loader import Config, ConfigError, load_config
from graph import GraphError, build_graph
from repo_apt import RepoError, load_repo_url
from repo_test import TestRepoError, load_test_repo


def print_config(cfg: Config) -> None:
    print(f"  package    : {cfg.package}")
    print(f"  repo       : {cfg.repo}")
    print(f"  repo_mode  : {cfg.repo_mode}")
    print(f"  output     : {cfg.output}")
    print(f"  ascii_tree : {cfg.ascii_tree}")


def load_repo(cfg: Config):
    # единая точка загрузки репозитория в зависимости от режима
    if cfg.repo_mode == "url":
        return load_repo_url(cfg.repo)
    return load_test_repo(cfg.repo)


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "config.csv"
    try:
        cfg = load_config(path)
    except ConfigError as e:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        return 2

    print_config(cfg)

    try:
        repo = load_repo(cfg)
    except (RepoError, TestRepoError) as e:
        print(f"[ОШИБКА РЕПОЗИТОРИЯ] {e}", file=sys.stderr)
        return 3

    try:
        edges, order, cycles = build_graph(repo, cfg.package)
    except GraphError as e:
        print(f"[ОШИБКА ГРАФА] {e}", file=sys.stderr)
        return 4

    # сводка
    total_edges = sum(len(v) for v in edges.values())
    print(f"\nУзлов в графе: {len(order)}")
    print(f"Рёбер в графе: {total_edges}")

    if cycles:
        print(f"Обнаружены циклы ({len(cycles)}):")
        for a, b in cycles:
            print(f"  {a} -> {b} (обратное ребро)")
    else:
        print("Циклов не обнаружено")

    # перечислили ребра для наглядности
    print("\nРёбра графа:")
    for src in order:
        for dst in edges.get(src, []):
            print(f"  {src} -> {dst}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
