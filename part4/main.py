import sys

from config_loader import Config, ConfigError, load_config
from graph import GraphError, build_graph
from ordering import load_order
from repo_apt import RepoError, load_repo_url
from repo_test import TestRepoError, load_test_repo


def print_config(cfg: Config) -> None:
    print(f"  package    : {cfg.package}")
    print(f"  repo       : {cfg.repo}")
    print(f"  repo_mode  : {cfg.repo_mode}")
    print(f"  output     : {cfg.output}")
    print(f"  ascii_tree : {cfg.ascii_tree}")


def load_repo(cfg: Config):
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
        edges, order_nodes, cycles = build_graph(repo, cfg.package)
    except GraphError as e:
        print(f"[ОШИБКА ГРАФА] {e}", file=sys.stderr)
        return 4

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

    seq, seq_cycles = load_order(repo, cfg.package)
    print(f"\nПорядок загрузки (зависимости раньше пакета):")
    for i, p in enumerate(seq, 1):
        print(f"  {i:>2}. {p}")
    if seq_cycles:
        print(
            f"  (порядок не является строго топологическим: "
            f"{len(seq_cycles)} цикл(ов))"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
