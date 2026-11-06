import sys

from config_loader import Config, ConfigError, load_config


def print_config(cfg: Config) -> None:
    print("=== Параметры конфигурации ===")
    print(f"  package    : {cfg.package}")
    print(f"  repo       : {cfg.repo}")
    print(f"  repo_mode  : {cfg.repo_mode}")
    print(f"  output     : {cfg.output}")
    print(f"  ascii_tree : {cfg.ascii_tree}")


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "config.csv"
    try:
        cfg = load_config(path)
    except ConfigError as e:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        return 2
    print_config(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
