# Модуль gzip для распаковки .gz-файлов из стандартной библиотеки
import gzip
# re — регулярные выражения (нужны для разбиения на станзы)
import re
# urllib.request — HTTP-запросы без сторонних библиотек
import urllib.request
# typing — подсказки типов
from typing import Dict, List


# Собственное исключение для ошибок репозитория
class RepoError(Exception):
    # Докстринг
    """Ошибка загрузки/разбора apt-репозитория."""
    # Пустое тело
    pass


# Функция скачивания и распаковки индекса репозитория
def fetch_packages_index(url: str) -> str:
    # Докстринг
    """Скачивает индекс репозитория по URL и возвращает его как текст."""
    # Оборачиваем сетевой вызов в try, чтобы дать понятную ошибку
    try:
        # Создаём Request с User-Agent (некоторые зеркала его требуют)
        req = urllib.request.Request(
            url, headers={"User-Agent": "depgraph/1.0"}
        )
        # Открываем URL; timeout=30 секунд, чтобы не висеть вечно
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Читаем всё тело ответа как bytes
            data = resp.read()
    # Ловим любую сетевую ошибку
    except Exception as e:
        # Превращаем в RepoError с контекстом
        raise RepoError(f"Не удалось загрузить индекс репозитория: {e}")

    # Пустой ответ — тоже ошибка (например, пустое зеркало)
    if not data:
        # Бросаем RepoError
        raise RepoError("Получен пустой ответ от репозитория")

    # gzip-магия: первые два байта 1f 8b; также проверяем расширение .gz
    if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
        # Пробуем распаковать
        try:
            # gzip.decompress возвращает распакованные bytes
            data = gzip.decompress(data)
        # Если данные не gzip — OSError
        except OSError as e:
            # Превращаем в RepoError
            raise RepoError(f"Ошибка распаковки gzip: {e}")

    # Пытаемся декодировать как UTF-8
    try:
        # Успех — возвращаем строку
        return data.decode("utf-8")
    # Если UTF-8 не подошёл — декодируем как latin-1 с заменой
    except UnicodeDecodeError:
        # latin-1 не падает никогда (1 байт = 1 символ)
        return data.decode("latin-1", errors="replace")


# Приватная функция разбора поля Depends
def _parse_dep_field(value: str) -> List[str]:
    # Докстринг с примером
    """
    'a (>=1), b | c, d:any' -> ['a', 'b', 'c', 'd'].
    """
    # Результат — список имён
    result: List[str] = []
    # Зависимости через запятую — это AND
    for group in value.split(","):
        # Внутри группы альтернативы через | — это OR
        for alt in group.split("|"):
            # Берём первое «слово», отрезаем версию/квалификатор
            name = (
                # Убираем пробелы по краям
                alt.strip()
                # Берём первое слово (отрезает версию после пробела)
                .split()[0]
                # Отрезаем " (>=...)"
                .split("(")[0]
                # Отрезаем ":any" / ":amd64"
                .split(":")[0]
                # Финальная зачистка пробелов
                .strip()
            )
            # Пустое имя (например, из ",,") пропускаем
            if name:
                # Добавляем в результат
                result.append(name)
    # Возвращаем список
    return result


# Публичная функция разбора всего текста Packages
def parse_packages(text: str) -> Dict[str, List[str]]:
    # Докстринг
    """Парсит текст Packages в {имя: [прямые зависимости]}."""
    # Результат — словарь
    result: Dict[str, List[str]] = {}

    # Станзы разделены одной или несколькими пустыми строками
    for stanza in re.split(r"\n\s*\n", text):
        # Пустая станза (например, в конце файла) — пропускаем
        if not stanza.strip():
            # Переходим к следующей
            continue

        # Логические строки: сюда склеим продолжения полей
        logical_lines: List[str] = []
        # Разбираем станзу построчно
        for line in stanza.splitlines():
            # Строка с ведущим пробелом/табом — продолжение предыдущего поля
            if line.startswith((" ", "\t")):
                # Если уже есть к чему приклеивать
                if logical_lines:
                    # Приклеиваем через пробел
                    logical_lines[-1] += " " + line.strip()
                # В любом случае переходим к следующей строке
                continue
            # Обычная строка — добавляем как есть
            logical_lines.append(line)

        # Имя пакета (пока неизвестно)
        name = None
        # Строка Depends (пока пустая)
        depends = ""
        # Идём по логическим строкам
        for line in logical_lines:
            # Строки без ':' — мусор, пропускаем
            if ":" not in line:
                # Следующая строка
                continue
            # Делим на ключ и значение по первому ':'
            key, _, val = line.partition(":")
            # Ключ приводим к нижнему регистру и обрезаем
            key = key.strip().lower()
            # Если это Package — запоминаем имя
            if key == "package":
                # Значение обрезаем
                name = val.strip()
            # Если это Depends — запоминаем зависимости
            elif key == "depends":
                # Значение обрезаем
                depends = val.strip()

        # Если имя нашли — сохраняем в результат
        if name:
            # Пустой Depends → пустой список
            result[name] = _parse_dep_field(depends) if depends else []

    # Возвращаем словарь всех пакетов
    return result


# Публичная функция — полный цикл загрузки по URL
def load_repo_url(url: str) -> Dict[str, List[str]]:
    # Докстринг
    """Скачивает, распаковывает и парсит индекс репозитория."""
    # Скачиваем и распаковываем в текст
    text = fetch_packages_index(url)
    # Парсим в словарь
    packages = parse_packages(text)
    # Если ни одного пакета не нашлось — почти наверняка URL не туда
    if not packages:
        # Бросаем ошибку с подсказкой
        raise RepoError(
            "Индекс репозитория не содержит ни одного пакета "
            "(возможно, URL указывает не на Packages.gz)"
        )
    # Возвращаем словарь
    return packages
