"""Модуль загрузки тестового репозитория."""
from typing import Dict, List


class TestRepoError(Exception):
    """Ошибка загрузки тестового репозитория."""


def _is_valid_name(text: str) -> bool:
    """Проверяет, что имя состоит из заглавных латинских букв."""
    return bool(text) and text.isalpha() and text.isupper()


def load_test_repo(path: str) -> Dict[str, List[str]]:
    """Читает файл 'A: B C' и возвращает словарь зависимостей."""
    repo = {}
    try:
        with open(path, encoding="utf-8") as file:
            for line_num, raw in enumerate(file, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    msg = f"Строка {line_num}: ожидался формат 'NAME: DEP'"
                    raise TestRepoError(msg)
                
                name, _, rest = line.partition(":")
                name = name.strip()
                
                if not _is_valid_name(name):
                    msg = f"Строка {line_num}: неверное имя '{name}'"
                    raise TestRepoError(msg)
                if name in repo:
                    msg = f"Строка {line_num}: повтор '{name}'"
                    raise TestRepoError(msg)
                
                deps = rest.split()
                for dep in deps:
                    if not _is_valid_name(dep):
                        msg = f"Строка {line_num}: неверная зависимость '{dep}'"
                        raise TestRepoError(msg)
                repo[name] = deps
    except FileNotFoundError:
        raise TestRepoError(f"Файл не найден: {path}")

    if not repo:
        raise TestRepoError(f"Репозиторий пуст: {path}")
    return repo
