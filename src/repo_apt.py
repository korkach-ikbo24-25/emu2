"""Модуль загрузки и разбора apt-репозитория."""
import gzip
import re
import urllib.request
from typing import Dict, List

TIMEOUT = 30
GZIP_MAGIC = b"\x1f\x8b"


class RepoError(Exception):
    """Ошибка загрузки/разбора репозитория."""


def fetch_packages_index(url: str) -> str:
    """Скачивает индекс репозитория и возвращает его как текст."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "depgraph/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
    except Exception as err:
        raise RepoError(f"Не удалось загрузить индекс: {err}")

    if not data:
        raise RepoError("Получен пустой ответ от репозитория")

    if url.endswith(".gz") or data[:2] == GZIP_MAGIC:
        try:
            data = gzip.decompress(data)
        except OSError as err:
            raise RepoError(f"Ошибка распаковки gzip: {err}")

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def _parse_dep_field(value: str) -> List[str]:
    """Разбирает поле Depends в список имен пакетов."""
    result = []
    for group in value.split(","):
        for alt in group.split("|"):
            name = (
                alt.strip()
                .split()[0]
                .split("(")[0]
                .split(":")[0]
                .strip()
            )
            if name:
                result.append(name)
    return result


def _merge_continuation_lines(stanza: str) -> List[str]:
    """Склеивает строки с ведущими пробелами (продолжения полей)."""
    logical = []
    for line in stanza.splitlines():
        if line.startswith((" ", "\t")):
            if logical:
                logical[-1] += " " + line.strip()
            continue
        logical.append(line)
    return logical


def _parse_stanza(stanza: str) -> tuple[str, List[str]]:
    """Извлекает имя пакета и список зависимостей из одной станзы."""
    name = None
    depends = ""
    for line in _merge_continuation_lines(stanza):
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        if key == "package":
            name = val.strip()
        elif key == "depends":
            depends = val.strip()

    deps = _parse_dep_field(depends) if depends else []
    return name, deps


def parse_packages(text: str) -> Dict[str, List[str]]:
    """Парсит текст Packages в словарь {имя: [зависимости]}."""
    result = {}
    for stanza in re.split(r"\n\s*\n", text):
        if not stanza.strip():
            continue
        name, deps = _parse_stanza(stanza)
        if name:
            result[name] = deps
    return result


def load_repo_url(url: str) -> Dict[str, List[str]]:
    """Скачивает, распаковывает и парсит индекс репозитория."""
    text = fetch_packages_index(url)
    packages = parse_packages(text)
    if not packages:
        raise RepoError("Индекс не содержит пакетов (проверьте URL)")
    return packages
