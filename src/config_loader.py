"""Модуль чтения и валидации CSV-конфигурации."""
import csv
import os
from dataclasses import dataclass
from urllib.parse import urlparse

VALID_KEYS = {"package", "repo", "repo_mode", "output", "ascii_tree"}
VALID_MODES = {"url", "test"}


class ConfigError(Exception):
    """Ошибка конфигурации с человекочитаемым сообщением."""


@dataclass
class Config:
    """Настройки приложения."""
    package: str
    repo: str
    repo_mode: str
    output: str
    ascii_tree: bool


def _parse_bool(value: str, key: str) -> bool:
    """Преобразует строку в boolean."""
    val = value.strip().lower()
    if val in ("true", "1", "yes", "y"):
        return True
    if val in ("false", "0", "no", "n"):
        return False
    msg = f"Параметр '{key}': ожидалось true/false, получено '{value}'"
    raise ConfigError(msg)


def _validate_package(name: str) -> None:
    """Проверяет имя пакета."""
    if not name:
        raise ConfigError("Параметр 'package' пуст")
    if not all(c.isalnum() or c in "+-._" for c in name):
        raise ConfigError(f"Недопустимое имя пакета: '{name}'")


def _validate_repo(repo: str, mode: str) -> None:
    """Проверяет URL или путь к файлу."""
    if not repo:
        raise ConfigError("Параметр 'repo' пуст")
    if mode == "url":
        parsed = urlparse(repo)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            msg = f"Некорректный URL: '{repo}'"
            raise ConfigError(msg)
    else:
        if not os.path.isfile(repo):
            msg = f"Файл тестового репозитория не найден: '{repo}'"
            raise ConfigError(msg)


def _validate_output(path: str) -> None:
    """Проверяет путь к выходному файлу."""
    if not path:
        raise ConfigError("Параметр 'output' пуст")
    if not path.lower().endswith(".svg"):
        msg = f"Имя выходного файла должно оканчиваться на .svg: '{path}'"
        raise ConfigError(msg)
    out_dir = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(out_dir):
        raise ConfigError(f"Каталог не существует: '{out_dir}'")


def _read_csv_data(path: str) -> dict[str, str]:
    """Читает ключи и значения из CSV."""
    raw = {}
    try:
        with open(path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")
            if reader.fieldnames != ["key", "value"]:
                raise ConfigError("CSV должен иметь заголовок 'key;value'")
            for line_num, row in enumerate(reader, start=2):
                key = (row.get("key") or "").strip()
                val = (row.get("value") or "").strip()
                if not key:
                    raise ConfigError(f"Строка {line_num}: пустой ключ")
                if key not in VALID_KEYS:
                    raise ConfigError(f"Строка {line_num}: ключ '{key}'")
                if key in raw:
                    raise ConfigError(f"Строка {line_num}: дубликат '{key}'")
                raw[key] = val
    except csv.Error as err:
        raise ConfigError(f"Ошибка разбора CSV: {err}")
    return raw


def load_config(path: str) -> Config:
    """Загружает и валидирует конфигурацию из файла."""
    if not os.path.isfile(path):
        raise ConfigError(f"Конфигурационный файл не найден: {path}")

    raw = _read_csv_data(path)
    missing = VALID_KEYS - raw.keys()
    if missing:
        raise ConfigError(f"Отсутствуют ключи: {sorted(missing)}")

    _validate_package(raw["package"])
    mode = raw["repo_mode"].lower()
    if mode not in VALID_MODES:
        raise ConfigError(f"repo_mode должен быть: {sorted(VALID_MODES)}")

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
