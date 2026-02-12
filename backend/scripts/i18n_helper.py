"""
i18n helper script to list non-English strings in the frontend codebase.

Usage:
  python backend/scripts/i18n_helper.py --root frontend/src --output report.txt

What it does:
  - Scans source files (ts/tsx/jsx/json/css optional) under the given root.
  - Detects lines containing non-ASCII characters (CJK, Cyrillic, etc.).
  - Outputs a report with file:line and the offending text segment.
  - Optionally exports a JSON template of detected strings for translation keys.

Notes:
  - This tool is read-only; it does not modify source files.
  - You can extend the script to auto-generate translation key suggestions.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

NON_ASCII_PATTERN = re.compile(r"[^\x00-\x7F]")


def iter_files(root: Path, exts: tuple[str, ...]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in exts:
            yield path


def find_non_english_lines(path: Path) -> list[tuple[int, str]]:
    results = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return results

    for idx, line in enumerate(text.splitlines(), 1):
        if NON_ASCII_PATTERN.search(line):
            results.append((idx, line.strip()))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan for non-English strings.")
    parser.add_argument("--root", type=Path, required=True, help="Root directory to scan (e.g., frontend/src)")
    parser.add_argument(
        "--exts",
        nargs="+",
        default=[".ts", ".tsx", ".js", ".jsx", ".json"],
        help="File extensions to include",
    )
    parser.add_argument("--output", type=Path, help="Optional path to write the report")
    parser.add_argument("--export-json", type=Path, help="Optional path to export JSON template")
    args = parser.parse_args()

    report_lines: list[str] = []
    export_entries: list[dict[str, str]] = []

    for file_path in iter_files(args.root, tuple(args.exts)):
        hits = find_non_english_lines(file_path)
        if not hits:
            continue
        for line_no, text in hits:
            line = f"{file_path.relative_to(args.root)}:{line_no}: {text}"
            report_lines.append(line)
            export_entries.append(
                {
                    "file": str(file_path.relative_to(args.root)),
                    "line": line_no,
                    "text": text,
                }
            )

    report = "\n".join(report_lines)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    if args.export_json:
        args.export_json.write_text(json.dumps(export_entries, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON export written to {args.export_json}")


if __name__ == "__main__":
    main()
