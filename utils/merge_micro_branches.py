#!/usr/bin/env python3
"""Сборщик микро-веток (Пакетные релизы).

Находит все локальные ветки с префиксом ``micro/`` и сливает их содержимое
в одну общую целевую ветку (по умолчанию ``feature/combined-release``),
после чего удаляет отработавшие микро-ветки.

Запуск (через uv):
    uv run python utils/merge_micro_branches.py
    uv run python utils/merge_micro_branches.py --dry-run
    uv run python utils/merge_micro_branches.py --target feature/my-release
    uv run python utils/merge_micro_branches.py --keep

Требования:
    - Git установлен и доступен в PATH.
    - Репозиторий инициализирован (``git init``) и есть хотя бы один коммит.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec: B404
import sys
from typing import List, Optional

MICRO_PREFIX = "micro/"
DEFAULT_TARGET = "feature/combined-release"


def run_git(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Выполнить git-команду и вернуть результат."""
    return subprocess.run(  # nosec: B603 B607
        ["git", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def get_current_branch() -> str:
    """Вернуть имя текущей ветки."""
    result = run_git(["branch", "--show-current"])
    return result.stdout.strip()


def list_micro_branches() -> List[str]:
    """Найти все локальные ветки с префиксом ``micro/``."""
    result = run_git(["branch", "--list", f"{MICRO_PREFIX}*"])
    branches = [
        line.strip().lstrip("* ").strip() for line in result.stdout.splitlines()
    ]
    return [b for b in branches if b]


def branch_exists(branch: str) -> bool:
    """Проверить, существует ли ветка локально."""
    result = run_git(
        ["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], check=False
    )
    return result.returncode == 0


def ensure_target_branch(target: str) -> None:
    """Создать целевую ветку, если её ещё нет (от текущей HEAD)."""
    if not branch_exists(target):
        print(f"  ➕ Создаю целевую ветку: {target}")
        run_git(["checkout", "-b", target])
    else:
        print(f"  ℹ️  Целевая ветка уже существует: {target}")


def squash_merge_branch(branch: str, target: str, dry_run: bool) -> bool:
    """Слить микро-ветку в целевую через ``git merge --squash``.

    Возвращает True, если слияние прошло успешно (или было бы успешным в dry-run).
    """
    print(f"\n  🔀 Сливаю: {branch} -> {target}")

    if dry_run:
        print(f"     (dry-run) git merge --squash {branch}")
        print(f"     (dry-run) git commit -m 'merge: {branch} into {target}'")
        return True

    # Переключаемся на целевую ветку
    run_git(["checkout", target])

    # Squash-слияние микро-ветки
    merge = run_git(["merge", "--squash", branch], check=False)
    if merge.returncode != 0:
        print(f"  ❌ Ошибка при squash-слиянии {branch}:")
        print(merge.stderr.strip())
        return False

    # Коммитим объединённые изменения
    commit = run_git(
        ["commit", "-m", f"merge: {branch} into {target}"],
        check=False,
    )
    if commit.returncode != 0:
        # Возможно, нет изменений для коммита (ветка уже слита)
        print(f"  ⚠️  Нет изменений для коммита из {branch} (уже слита?)")
        return True

    print(f"  ✅ {branch} успешно слита в {target}")
    return True


def delete_branch(branch: str, dry_run: bool) -> None:
    """Удалить микро-ветку."""
    if dry_run:
        print(f"     (dry-run) git branch -D {branch}")
        return

    result = run_git(["branch", "-D", branch], check=False)
    if result.returncode == 0:
        print(f"  🗑️  Удалена ветка: {branch}")
    else:
        print(f"  ⚠️  Не удалось удалить {branch}: {result.stderr.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Сборщик микро-веток: сливает micro/* в одну целевую ветку.",
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"Целевая ветка (по умолчанию: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать план действий без внесения изменений",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Не удалять микро-ветки после слияния",
    )
    args = parser.parse_args()

    micro_branches = list_micro_branches()

    if not micro_branches:
        print("ℹ️  Микро-ветки не найдены. Ничего делать не нужно.")
        return 0

    print(f"Найдено микро-веток: {len(micro_branches)}")
    for branch in micro_branches:
        print(f"  - {branch}")

    if args.dry_run:
        print("\n🧪 РЕЖИМ DRY-RUN — изменения не вносятся\n")

    current = get_current_branch()
    print(f"\nТекущая ветка: {current}")
    print(f"Целевая ветка: {args.target}")

    # Создаём целевую ветку (в dry-run только показываем)
    if args.dry_run:
        print(f"  (dry-run) git checkout -b {args.target}  (если не существует)")
    else:
        ensure_target_branch(args.target)

    # Сливаем каждую микро-ветку
    merged: List[str] = []
    failed: List[str] = []

    for branch in micro_branches:
        if branch == args.target:
            print(f"  ⏭️  Пропускаю {branch} — это целевая ветка")
            continue

        if squash_merge_branch(branch, args.target, args.dry_run):
            merged.append(branch)
        else:
            failed.append(branch)

    # Удаляем отработавшие микро-ветки
    if not args.keep:
        print("\n🗑️  Удаление отработавших микро-веток:")
        for branch in merged:
            delete_branch(branch, args.dry_run)

    # Возвращаемся на исходную ветку (если не dry-run и не остались на target)
    if not args.dry_run and current and current != args.target:
        print(f"\n↩️  Возвращаюсь на ветку: {current}")
        run_git(["checkout", current])

    # Итог
    print("\n" + "=" * 50)
    print("📊 ИТОГ:")
    print(f"  ✅ Успешно слито: {len(merged)}")
    if failed:
        print(f"  ❌ Ошибки: {len(failed)}")
        for branch in failed:
            print(f"     - {branch}")
        return 1

    if args.dry_run:
        print("  (dry-run — реальные изменения не вносились)")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
