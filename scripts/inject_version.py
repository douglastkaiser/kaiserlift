#!/usr/bin/env python
from __future__ import annotations

import subprocess
from pathlib import Path

from setuptools_scm import get_version


def _read_version() -> str:
    """Read the project version from git tags using setuptools-scm.

    This avoids importing :mod:`kaiserlift`, which may not yet be installable
    when this script runs (e.g. in CI before the package is built).
    """
    root = Path(__file__).resolve().parent.parent
    return get_version(root=root)


def _get_git_hash() -> str:
    """Get the short git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _get_git_hash_full() -> str:
    """Get the full git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> None:
    """Write the package version and git hash to ``client/version.js``."""
    out = Path(__file__).resolve().parent.parent / "client" / "version.js"
    version = _read_version()
    git_hash = _get_git_hash()
    git_hash_full = _get_git_hash_full()
    content = f'''export const VERSION = "{version}";
export const GIT_HASH = "{git_hash}";
export const GIT_HASH_FULL = "{git_hash_full}";
'''
    out.write_text(content, encoding="utf-8")
    print(f"Wrote version {version} (commit {git_hash}) to {out}")


if __name__ == "__main__":
    main()
