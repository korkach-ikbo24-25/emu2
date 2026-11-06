import gzip
import re
import urllib.request
from typing import Dict, List


class RepoError(Exception):
    #oшибка загрузки/разбора apt-репозитория.
    pass


def fetch_packages_index(url: str) -> str:
    #скачивает индекс репозитория по URL и возвращает его как текст
    #автоматически распаковывает gzip, если данные сжаты
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "depgraph/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        raise RepoError(f"Не удалось загрузить индекс репозитория: {e}")

    if not data:
        raise RepoError("Получен пустой ответ от репозитория")

    # gzip: 0x1f 0x8b
    if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            data = gzip.decompress(data)
        except OSError as e:
            raise RepoError(f"Ошибка распаковки gzip: {e}")

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        # некоторые индексы содержат latin-1
        return data.decode("latin-1", errors="replace")


def _parse_dep_field(value: str) -> List[str]:
    """
    Разбирает поле Depends в список имён пакетов.
    'a (>=1), b | c, d:any' -> ['a', 'b', 'c', 'd']
    Альтернативы (через |) включаются все — их выбор уже дело менеджера.
    """
    result: List[str] = []
    for group in value.split(","):
        for alt in group.split("|"):
            name = (
                alt.strip()
                .split()[0]           # отрезает версию после пробела
                .split("(")[0]        # отрезает " (>=...)"
                .split(":")[0]        # отрезает ":any" / ":amd64"
                .strip()
            )
            if name:
                result.append(name)
    return result


def parse_packages(text: str) -> Dict[str, List[str]]:
    #парсит текст Packages в словарь {имя_пакета: [прямые_зависимости]}.

    result: Dict[str, List[str]] = {}

    for stanza in re.split(r"\n\s*\n", text):
        if not stanza.strip():
            continue

        # собираем логические строки: склеиваем продолжения с предыдущей
        logical_lines: List[str] = []
        for line in stanza.splitlines():
            if line.startswith((" ", "\t")):
                if logical_lines:
                    # продолжение: добавляем через пробел к последней строке
                    logical_lines[-1] += " " + line.strip()
                continue
            logical_lines.append(line)

        name = None
        depends = ""
        for line in logical_lines:
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            if key == "package":
                name = val.strip()
            elif key == "depends":
                depends = val.strip()

        if name:
            result[name] = _parse_dep_field(depends) if depends else []

    return result


def load_repo_url(url: str) -> Dict[str, List[str]]:
    # скачивает распаковывает и парсит
    text = fetch_packages_index(url)
    packages = parse_packages(text)
    if not packages:
        raise RepoError(
            "Индекс репозитория не содержит ни одного пакета "
            "(возможно, URL указывает не на Packages.gz)"
        )
    return packages
