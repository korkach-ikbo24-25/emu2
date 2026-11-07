from typing import Dict, List


class TestRepoError(Exception):
    pass


def _is_package_name(s: str) -> bool:
    return bool(s) and s.isalpha() and s.isupper()


def load_test_repo(path: str) -> Dict[str, List[str]]:
    # читает файл вида:
    #     A: B C
    #     B: D
    #     D:
    # возвращает {имя: [зависимости]}
    repo: Dict[str, List[str]] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise TestRepoError(
                        f"Строка {lineno}: ожидался формат 'NAME: DEP1 DEP2'"
                    )
                name, _, rest = line.partition(":")
                name = name.strip()
                if not _is_package_name(name):
                    raise TestRepoError(
                        f"Строка {lineno}: имя пакета '{name}' должно "
                        f"состоять из заглавных латинских букв"
                    )
                if name in repo:
                    raise TestRepoError(
                        f"Строка {lineno}: повторное определение пакета '{name}'"
                    )
                deps = rest.split()
                for d in deps:
                    if not _is_package_name(d):
                        raise TestRepoError(
                            f"Строка {lineno}: зависимость '{d}' должна "
                            f"состоять из заглавных латинских букв"
                        )
                repo[name] = deps
    except FileNotFoundError:
        raise TestRepoError(f"Файл тестового репозитория не найден: {path}")

    if not repo:
        raise TestRepoError(f"Тестовый репозиторий пуст: {path}")
    return repo
