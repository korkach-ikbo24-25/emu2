# typing — подсказки типов
from typing import Dict, List


# Собственное исключение для тестового репозитория
class TestRepoError(Exception):
    # Докстринг
    """Ошибка загрузки тестового репозитория."""
    # Пустое тело
    pass


# Приватная функция — проверка, что строка — допустимое имя пакета
def _is_package_name(s: str) -> bool:
    # Непустая, все символы — буквы, и все — заглавные
    return bool(s) and s.isalpha() and s.isupper()


# Публичная функция — чтение тестового файла
def load_test_repo(path: str) -> Dict[str, List[str]]:
    # Докстринг
    """
    Читает файл вида:
        A: B C
        B: D
        D:
    Возвращает {имя: [зависимости]}.
    """
    # Результат — словарь
    repo: Dict[str, List[str]] = {}
    # Оборачиваем открытие в try, чтобы дать понятную ошибку
    try:
        # Открываем файл в UTF-8
        with open(path, encoding="utf-8") as f:
            # Идём по строкам с номерами (нумерация с 1)
            for lineno, raw in enumerate(f, 1):
                # Обрезаем пробелы/переводы строк
                line = raw.strip()
                # Пустая строка или комментарий — пропускаем
                if not line or line.startswith("#"):
                    # Следующая строка
                    continue
                # Формат требует двоеточия
                if ":" not in line:
                    # Иначе — ошибка с номером строки
                    raise TestRepoError(
                        f"Строка {lineno}: ожидался формат 'NAME: DEP1 DEP2'"
                    )
                # Делим на имя и остаток по первому ':'
                name, _, rest = line.partition(":")
                # Имя без пробелов
                name = name.strip()
                # Имя должно быть ЗАГЛАВНЫМИ латинскими буквами
                if not _is_package_name(name):
                    # Иначе — ошибка
                    raise TestRepoError(
                        f"Строка {lineno}: имя пакета '{name}' должно "
                        f"состоять из заглавных латинских букв"
                    )
                # Повторное определение пакета недопустимо
                if name in repo:
                    # Ошибка
                    raise TestRepoError(
                        f"Строка {lineno}: повторное определение пакета '{name}'"
                    )
                # Разбиваем остаток по пробелам на зависимости
                deps = rest.split()
                # Каждая зависимость тоже должна быть ЗАГЛАВНЫМИ
                for d in deps:
                    # Проверяем
                    if not _is_package_name(d):
                        # Иначе — ошибка
                        raise TestRepoError(
                            f"Строка {lineno}: зависимость '{d}' должна "
                            f"состоять из заглавных латинских букв"
                        )
                # Сохраняем в словарь
                repo[name] = deps
    # Файл не найден — отдельная ошибка
    except FileNotFoundError:
        # С сообщением о пути
        raise TestRepoError(f"Файл тестового репозитория не найден: {path}")

    # Пустой словарь — тоже ошибка
    if not repo:
        # Бросаем
        raise TestRepoError(f"Тестовый репозиторий пуст: {path}")
    # Возвращаем словарь
    return repo
