import sys

from config_loader import Config, ConfigError, load_config
from repo_apt import RepoError, load_repo_url

def print_config(cfg: Config) -> None:
    print(f"  package    : {cfg.package}")
    print(f"  repo       : {cfg.repo}")
    print(f"  repo_mode  : {cfg.repo_mode}")
    print(f"  output     : {cfg.output}")
    print(f"  ascii_tree : {cfg.ascii_tree}")


def print_direct_deps(cfg: Config) -> int:
    try:
        repo = load_repo_url(cfg.repo)
    except RepoError as e:
        print(f"[ОШИБКА РЕПОЗИТОРИЯ] {e}", file=sys.stderr)
        return 3

    direct = repo.get(cfg.package)
    if direct is None:
        print(
            f"[ОШИБКА] Пакет '{cfg.package}' не найден в индексе репозитория",
            file=sys.stderr,
        )
        return 3

    print(f"\nПрямые зависимости '{cfg.package}':")
    if not direct:
        print("  (нет)")
    else:
        for d in direct:
            print(f"  - {d}")
    return 0


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "config.csv"
    try:
        cfg = load_config(path)
    except ConfigError as e:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        return 2

    print_config(cfg)

    if cfg.repo_mode == "url":
        return print_direct_deps(cfg)

    print(
        "[ИНФО] repo_mode=test — загрузка тестового репозитория "
        "будет реализована на этапе 3",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
