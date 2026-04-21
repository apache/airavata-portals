#!/usr/bin/env python3
"""Audit pyproject.toml dependency pins for rationale comments.

Rule: every dependency string containing `<` (a version upper bound) must
have either an inline `# ...` comment on the same line OR a preceding
comment line that starts with `#`.

Exits 0 with "OK: every `<` pin has a rationale comment" if clean.
Exits 1 listing each violation (`pyproject.toml:<line>: <source>`) otherwise.

Run from the directory that contains pyproject.toml.
"""

from __future__ import annotations

import pathlib
import sys


def main() -> int:
    path = pathlib.Path("pyproject.toml")
    if not path.exists():
        print("pin_audit: pyproject.toml not found in cwd", file=sys.stderr)
        return 2

    lines = path.read_text().splitlines()
    violations: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith('"') or stripped.startswith("'")):
            continue
        if "<" not in line:
            continue
        has_inline_comment = "#" in line
        prev_line = lines[i - 1].strip() if i > 0 else ""
        has_prev_comment = prev_line.startswith("#")
        if not (has_inline_comment or has_prev_comment):
            violations.append((i + 1, line.rstrip()))

    if violations:
        print("pyproject.toml pin audit violations:")
        for line_no, src in violations:
            print(f"  pyproject.toml:{line_no}: {src}")
        return 1

    print("OK: every `<` pin has a rationale comment")
    return 0


if __name__ == "__main__":
    sys.exit(main())
