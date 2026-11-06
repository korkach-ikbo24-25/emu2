#отвечает за чтение csv
import csv
import os
from dataclasses import dataclass
from urllib.parse import urlparse


VALID_KEYS = {"package", "repo", "repo_mode", "output", "ascii_tree"}
VALID_MODES = {"url", "test"}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    package: str
    repo: str
    repo_mode: str
    output: str
    ascii_tree: bool


def _parse_bool(value: str, key: str) -> bool:
    v = value.strip().lower()
    if v in ("true", "1", "yes", "y"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    raise ConfigError(
        f"Параметр '{key}': ожидалось true/false, получено '{value}'"
    )


def _validate_package(name: str) -> None:
    if not name:
        raise ConfigError("Параметр 'package' пуст")
    # разрешённые символы в именах deb-пакетов: буквы, цифры, + - . _
    if not all(c.isalnum() or c in "+-._" for c in name):
        raise ConfigError(f"Недопустимое имя пакета: '{name}'")


def _validate_repo(repo: str, mode: str) -> None:
    if not repo:
        raise ConfigError("Параметр 'repo' пуст")
    if mode == "url":
        p = urlparse(repo)
        if p.scheme not in ("http", "https") or not p.netloc:
            raise ConfigError(
                f"Некорректный URL репозитория: '{repo}' "
                f"(ожидался http(s)://host/...)"
            )
    else:  # test
        if not os.path.isfile(repo):
            raise ConfigError(
                f"Файл тестового репозитория не найден: '{repo}'"
            )


def _validate_output(path: str) -> None:
    if not path:
        raise ConfigError("Параметр 'output' пуст")
    if not path.lower().endswith(".svg"):
        raise ConfigError(
            f"Имя выходного файла должно оканчиваться на .svg: '{path}'"
        )
    out_dir = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(out_dir):
        raise ConfigError(
            f"Каталог для выходного файла не существует: '{out_dir}'"
        )


def load_config(path: str) -> Config:
    if not os.path.isfile(path):
        raise ConfigError(f"Конфигурационный файл не найден: {path}")

    raw: dict[str, str] = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            if reader.fieldnames != ["key", "value"]:
                raise ConfigError(
                    "CSV должен содержать ровно заголовок 'key;value'"
                )
            for lineno, row in enumerate(reader, start=2):
                k = (row.get("key") or "").strip()
                v = (row.get("value") or "").strip()
                if not k:
                    raise ConfigError(f"Строка {lineno}: пустой ключ")
                if k not in VALID_KEYS:
                    raise ConfigError(
                        f"Строка {lineno}: неизвестный ключ '{k}'"
                    )
                if k in raw:
                    raise ConfigError(
                        f"Строка {lineno}: дубликат ключа '{k}'"
                    )
                raw[k] = v
    except csv.Error as e:
        raise ConfigError(f"Ошибка разбора CSV: {e}")

    # проверяет полноту набора ключей
    missing = VALID_KEYS - raw.keys()
    if missing:
        raise ConfigError(
            f"Отсутствуют обязательные ключи: {sorted(missing)}"
        )

    # валидация каждого параметра
    _validate_package(raw["package"])

    mode = raw["repo_mode"].lower()
    if mode not in VALID_MODES:
        raise ConfigError(
            f"repo_mode должен быть одним из {sorted(VALID_MODES)}, "
            f"получено '{raw['repo_mode']}'"
        )

    _validate_repo(raw["repo"], mode)
    _validate_output(raw["output"])
    ascii_tree = _parse_bool(raw["ascii_tree"], "ascii_tree")

    return Config(
        package=raw["package"],
        repo=raw["repo"],
        repo_mode=mode,
        output=raw["output"],
        ascii_tree=ascii_tree,
    )
