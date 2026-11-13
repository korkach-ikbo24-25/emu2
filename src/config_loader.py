# Импортируем модуль csv для чтения/записи CSV-файлов из стандартной библиотеки
import csv
# Импортируем os для проверки существования файлов и каталогов
import os
# Импортируем dataclass — декоратор для краткого объявления классов-данных
from dataclasses import dataclass
# Импортируем urlparse — разбор URL на компоненты (scheme, netloc, path)
from urllib.parse import urlparse


# Множество допустимых ключей конфигурации; любой другой ключ — ошибка
VALID_KEYS = {"package", "repo", "repo_mode", "output", "ascii_tree"}
# Множество допустимых значений repo_mode: реальный URL или тестовый файл
VALID_MODES = {"url", "test"}


# Собственное исключение для ошибок конфигурации
class ConfigError(Exception):
    # Строка документации (docstring) — краткое описание класса
    """Ошибка конфигурации с человекочитаемым сообщением."""
    # pass означает «тело пустое»; всё поведение наследуется от Exception
    pass


# Декоратор @dataclass автоматически создаёт __init__, __repr__, __eq__
@dataclass
class Config:
    # Имя анализируемого пакета (строка)
    package: str
    # URL репозитория или путь к тестовому файлу
    repo: str
    # Режим работы с репозиторием: "url" или "test"
    repo_mode: str
    # Имя выходного SVG-файла
    output: str
    # Флаг: печатать ли ASCII-дерево
    ascii_tree: bool


# Приватная функция (префикс _) — разбор булева значения из строки
def _parse_bool(value: str, key: str) -> bool:
    # Приводим к нижнему регистру и убираем пробелы по краям
    v = value.strip().lower()
    # Принимаем несколько «истинных» написаний
    if v in ("true", "1", "yes", "y"):
        # Возвращаем True
        return True
    # Принимаем несколько «ложных» написаний
    if v in ("false", "0", "no", "n"):
        # Возвращаем False
        return False
    # Любое другое значение — ошибка с указанием ключа
    raise ConfigError(
        f"Параметр '{key}': ожидалось true/false, получено '{value}'"
    )


# Приватная функция — проверка имени пакета
def _validate_package(name: str) -> None:
    # Пустое имя недопустимо
    if not name:
        # Бросаем ошибку конфигурации
        raise ConfigError("Параметр 'package' пуст")
    # Проверяем каждый символ: буква/цифра или один из +-._
    if not all(c.isalnum() or c in "+-._" for c in name):
        # Если есть недопустимый символ — ошибка
        raise ConfigError(f"Недопустимое имя пакета: '{name}'")


# Приватная функция — проверка источника репозитория
def _validate_repo(repo: str, mode: str) -> None:
    # Пустой путь/URL недопустим
    if not repo:
        # Бросаем ошибку
        raise ConfigError("Параметр 'repo' пуст")
    # В режиме url проверяем схему и наличие хоста
    if mode == "url":
        # Разбираем URL на компоненты
        p = urlparse(repo)
        # Схема должна быть http или https, хост — непустым
        if p.scheme not in ("http", "https") or not p.netloc:
            # Если нет — ошибка с подсказкой
            raise ConfigError(
                f"Некорректный URL репозитория: '{repo}' "
                f"(ожидался http(s)://host/...)"
            )
    # В режиме test путь должен указывать на существующий файл
    else:  # test
        # Проверяем, что это действительно файл
        if not os.path.isfile(repo):
            # Если нет — ошибка
            raise ConfigError(
                f"Файл тестового репозитория не найден: '{repo}'"
            )


# Приватная функция — проверка имени выходного файла
def _validate_output(path: str) -> None:
    # Пустой путь недопустим
    if not path:
        # Ошибка
        raise ConfigError("Параметр 'output' пуст")
    # Требуем расширение .svg (этап 5 сохраняет SVG)
    if not path.lower().endswith(".svg"):
        # Если расширение другое — ошибка
        raise ConfigError(
            f"Имя выходного файла должно оканчиваться на .svg: '{path}'"
        )
    # Берём абсолютный путь и выделяем каталог
    out_dir = os.path.dirname(os.path.abspath(path))
    # Каталог должен существовать (иначе dot не сможет записать файл)
    if not os.path.isdir(out_dir):
        # Иначе — ошибка
        raise ConfigError(
            f"Каталог для выходного файла не существует: '{out_dir}'"
        )


# Публичная функция — загрузка и валидация конфигурации
def load_config(path: str) -> Config:
    # Если файл не существует — сразу ошибка
    if not os.path.isfile(path):
        # Сообщение с путём
        raise ConfigError(f"Конфигурационный файл не найден: {path}")

    # Словарь для «сырых» пар ключ-значение из CSV
    raw: dict[str, str] = {}
    # Оборачиваем чтение в try, чтобы поймать ошибки csv
    try:
        # Открываем файл в режиме чтения, newline='' — правильно для csv
        with open(path, newline="", encoding="utf-8") as f:
            # Создаём DictReader с разделителем ';'
            reader = csv.DictReader(f, delimiter=";")
            # Проверяем, что заголовок ровно ['key', 'value']
            if reader.fieldnames != ["key", "value"]:
                # Иначе — понятная ошибка
                raise ConfigError(
                    "CSV должен содержать ровно заголовок 'key;value'"
                )
            # Перебираем строки начиная со 2-й (1-я — заголовок)
            for lineno, row in enumerate(reader, start=2):
                # Берём ключ, обрезаем пробелы; None → пустая строка
                k = (row.get("key") or "").strip()
                # Берём значение, обрезаем пробелы
                v = (row.get("value") or "").strip()
                # Пустой ключ недопустим
                if not k:
                    # Ошибка с номером строки
                    raise ConfigError(f"Строка {lineno}: пустой ключ")
                # Ключ должен быть из VALID_KEYS
                if k not in VALID_KEYS:
                    # Иначе — ошибка «неизвестный ключ»
                    raise ConfigError(
                        f"Строка {lineno}: неизвестный ключ '{k}'"
                    )
                # Дубликат ключа недопустим
                if k in raw:
                    # Ошибка
                    raise ConfigError(
                        f"Строка {lineno}: дубликат ключа '{k}'"
                    )
                # Сохраняем пару в словарь
                raw[k] = v
    # Ловим ошибки модуля csv (например, битые кавычки)
    except csv.Error as e:
        # Превращаем в нашу ошибку конфигурации
        raise ConfigError(f"Ошибка разбора CSV: {e}")

    # Считаем, каких ключей не хватает
    missing = VALID_KEYS - raw.keys()
    # Если что-то отсутствует — ошибка со списком
    if missing:
        # sorted — для стабильного порядка в сообщении
        raise ConfigError(
            f"Отсутствуют обязательные ключи: {sorted(missing)}"
        )

    # Валидируем package
    _validate_package(raw["package"])

    # Нормализуем repo_mode к нижнему регистру
    mode = raw["repo_mode"].lower()
    # Проверяем, что режим допустим
    if mode not in VALID_MODES:
        # Иначе — ошибка
        raise ConfigError(
            f"repo_mode должен быть одним из {sorted(VALID_MODES)}, "
            f"получено '{raw['repo_mode']}'"
        )

    # Валидируем repo с учётом режима
    _validate_repo(raw["repo"], mode)
    # Валидируем output
    _validate_output(raw["output"])
    # Парсим ascii_tree в bool
    ascii_tree = _parse_bool(raw["ascii_tree"], "ascii_tree")

    # Возвращаем заполненный dataclass Config
    return Config(
        # Имя пакета
        package=raw["package"],
        # Источник репозитория
        repo=raw["repo"],
        # Нормализованный режим
        repo_mode=mode,
        # Имя выходного файла
        output=raw["output"],
        # Флаг ASCII-дерева
        ascii_tree=ascii_tree,
    )
