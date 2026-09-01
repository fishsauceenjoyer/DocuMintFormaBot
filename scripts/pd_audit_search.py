"""Full-text search for personal data (PD) fields across the project.

Scans all source/config/doc files for PD-related keywords (English and
Russian) and writes a structured report to ``docs/PD_AUDIT.md`` so that
removal tasks (Epic 1) can reference exact files and line numbers.

Usage:
    uv run python scripts/pd_audit_search.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "docs" / "PD_AUDIT.md"

# Keywords to search (word-boundary aware to avoid false positives like
# "running" matching "inn").
EN_PATTERN = re.compile(
    r"\b(passport_number|passport|snils|date_of_birth|place_of_birth|inn|"
    r"address|registration)\b",
    re.IGNORECASE,
)
RU_PATTERN = re.compile(
    r"\b(паспорт\w*|инн\b|снилс\w*|адрес\w*|регистраци\w*|дата\s+рождения)\b",
    re.IGNORECASE,
)

SKIP_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "allure-results",
    "htmlcov",
    "node_modules",
    ".idea",
    ".vscode",
}

EXTENSIONS = {
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".js",
    ".md",
    ".txt",
    ".cfg",
    ".toml",
    ".ini",
}


def iter_files() -> list[Path]:
    """Collect all project files eligible for scanning."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in EXTENSIONS:
                files.append(path)
    return sorted(files)


def scan_file(path: Path) -> dict[str, list[tuple[int, str]]]:
    """Return {keyword: [(line_no, line_text), ...]} for one file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}

    hits: dict[str, list[tuple[int, str]]] = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in EN_PATTERN.finditer(line):
            keyword = match.group(0).lower()
            hits.setdefault(keyword, []).append((line_no, line.strip()))
        for match in RU_PATTERN.finditer(line):
            keyword = match.group(0).lower()
            hits.setdefault(keyword, []).append((line_no, line.strip()))
    return hits


def main() -> None:
    files = iter_files()
    report: list[str] = [
        "# 🔒 PD Audit — полнотекстовый поиск персональных данных",
        "",
        "Автогенерировано скриптом `scripts/pd_audit_search.py` (Эпик 1, задача 1.1).",
        "",
        f"Просканировано файлов: **{len(files)}**.",
        "",
        "Ключевые слова: passport, passport_number, inn, snils, address,",
        "registration, date_of_birth, place_of_birth, паспорт, инн, снилс,",
        "адрес, регистрация, дата рождения.",
        "",
    ]

    total_hits = 0
    files_with_hits = 0

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        hits = scan_file(path)
        if not hits:
            continue
        files_with_hits += 1
        report.append(f"## `{rel}`")
        report.append("")
        for keyword in sorted(hits):
            occurrences = hits[keyword]
            total_hits += len(occurrences)
            report.append(
                f"### Ключевое слово: `{keyword}` ({len(occurrences)} совпадений)"
            )
            report.append("")
            for line_no, line_text in occurrences[:50]:
                truncated = line_text[:160] + ("…" if len(line_text) > 160 else "")
                report.append(f"- L{line_no}: `{truncated}`")
            if len(occurrences) > 50:
                report.append(f"- … и ещё {len(occurrences) - 50} совпадений")
            report.append("")

    report.append("## 📊 Итоговая статистика")
    report.append("")
    report.append(f"- Файлов с совпадениями: **{files_with_hits}**")
    report.append(f"- Всего совпадений: **{total_hits}**")
    report.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    print(
        f"Files scanned: {len(files)}, files with hits: {files_with_hits}, total hits: {total_hits}"
    )


if __name__ == "__main__":
    main()
