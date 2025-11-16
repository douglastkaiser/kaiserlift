#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

from setuptools_scm import get_version


def _read_version() -> str:
    """Read the project version from git tags using setuptools-scm.

    This avoids importing :mod:`kaiserlift`, which may not yet be installable
    when this script runs (e.g. in CI before the package is built).
    """
    root = Path(__file__).resolve().parent.parent
    return get_version(root=root)


def main() -> None:
    """Write the package version to ``client/version.js``."""
    out = Path(__file__).resolve().parent.parent / "client" / "version.js"
    out.write_text(f'export const VERSION = "{_read_version()}";\n', encoding="utf-8")


if __name__ == "__main__":
    main()
