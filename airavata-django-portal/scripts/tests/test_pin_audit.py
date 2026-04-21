"""Unit tests for scripts/pin_audit.py.

The script enforces: every dependency string in pyproject.toml that contains
a `<` version upper bound must have either an inline `# ...` comment on the
same line OR a preceding comment line that starts with `#`.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def _run(tmp_path: Path, toml: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pyproject.toml").write_text(toml)
    script = Path(__file__).resolve().parents[1] / "pin_audit.py"
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def test_no_pins_passes(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        textwrap.dedent(
            """\
            [project]
            dependencies = [
                "requests>=2",
                "Django>=5.1",
            ]
            """
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_pin_with_inline_comment_passes(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        textwrap.dedent(
            """\
            [project]
            dependencies = [
                "Django>=5.1,<5.2",  # LTS series
            ]
            """
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pin_with_preceding_comment_passes(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        textwrap.dedent(
            """\
            [project]
            dependencies = [
                # LTS series
                "Django>=5.1,<5.2",
            ]
            """
        ),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pin_without_comment_fails(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        textwrap.dedent(
            """\
            [project]
            dependencies = [
                "Django>=5.1,<5.2",
            ]
            """
        ),
    )
    assert result.returncode == 1
    assert "pyproject.toml:" in result.stdout


def test_multiple_violations_all_reported(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        textwrap.dedent(
            """\
            [project]
            dependencies = [
                "Django>=5.1,<5.2",
                "wagtail>=6.3,<7",
            ]
            """
        ),
    )
    assert result.returncode == 1
    assert result.stdout.count("pyproject.toml:") == 2
