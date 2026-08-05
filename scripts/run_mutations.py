"""Native AST-based mutation runner for data/business_config.py.

Mutates 3 simple targets:
1. DELIVERY_PRICE_PLN = 20 -> 0
2. DELIVERY_PRICE_EUR = 5 -> 0
3. PASSPORT_NUMBER_PATTERN regex -> different pattern

Runs `uv run pytest` for each mutant and reports killed/survived.
"""
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_FILE = REPO_ROOT / "data" / "business_config.py"
ORIGINAL_CODE = TARGET_FILE.read_text(encoding="utf-8")

MUTATIONS = [
    {
        "name": "set DELIVERY_PRICE_PLN to 0",
        "find": "DELIVERY_PRICE_PLN: int = 20",
        "replace": "DELIVERY_PRICE_PLN: int = 0",
    },
    {
        "name": "set DELIVERY_PRICE_EUR to 0",
        "find": "DELIVERY_PRICE_EUR: int = 5",
        "replace": "DELIVERY_PRICE_EUR: int = 0",
    },
    {
        "name": "change PASSPORT_NUMBER_PATTERN regex",
        "find": "PASSPORT_NUMBER_PATTERN: str = r\"^[A-Z0-9\\s\\-\\.\\/]{3,30}$\"",
        "replace": "PASSPORT_NUMBER_PATTERN: str = r\"^[A-Z0-9]{3,30}$\"",
    },
]


def apply_mutation(source: str, find: str, replace: str) -> str:
    if find not in source:
        raise RuntimeError(f"Mutation anchor not found: {find}")
    return source.replace(find, replace, 1)


def run_pytest() -> tuple[int, str]:
    proc = subprocess.run(
        ["uv", "run", "pytest"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=False,
    )
    return proc.returncode, proc.stdout + proc.stdout


def main() -> int:
    if not TARGET_FILE.exists():
        print(f"Target file not found: {TARGET_FILE}")
        return 2

    results: list[dict] = []

    for mutation in MUTATIONS:
        mutated = apply_mutation(ORIGINAL_CODE, mutation["find"], mutation["replace"])

        tmp_path = TARGET_FILE.with_suffix(".py.mutated")
        tmp_path.write_text(mutated, encoding="utf-8")
        shutil.move(str(tmp_path), str(TARGET_FILE))

        try:
            code, output = run_pytest()
            killed = code != 0
            results.append(
                {
                    "name": mutation["name"],
                    "killed": killed,
                    "returncode": code,
                }
            )
            print(f"MUTATION: {mutation['name']}")
            print(f"  pytest exit code: {code}")
            print(f"  result: {'KILLED' if killed else 'SURVIVED'}")
        finally:
            TARGET_FILE.write_text(ORIGINAL_CODE, encoding="utf-8")

    total = len(results)
    killed = sum(1 for r in results if r["killed"])
    survived = total - killed
    score = (killed / total * 100) if total else 0.0

    print("\n=== MUTATION REPORT ===")
    print(f"total mutants : {total}")
    print(f"killed       : {killed}")
    print(f"survived     : {survived}")
    print(f"mutation score: {score:.2f}%")

    return 0 if killed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())