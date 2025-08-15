#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

from kaiserlift import __version__


def main() -> None:
    """Write the package version to ``client/version.js``."""
    out = Path(__file__).resolve().parent.parent / "client" / "version.js"
    out.write_text(f'export const VERSION = "{__version__}";\n', encoding="utf-8")


if __name__ == "__main__":
    main()
