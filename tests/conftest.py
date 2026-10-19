"""Tests use the installed package; install an editable build for development.

Do not prepend the checkout to sys.path: wheel validation must exercise the
installed distribution rather than silently falling back to repository code.
"""

import os
from pathlib import Path

import kaiserlift


def pytest_sessionstart(session):
    """Fail wheel validation if any runner has imported the local checkout."""
    expected = os.environ.get("EXPECTED_PACKAGE")
    if expected and Path(kaiserlift.__file__).resolve() != Path(expected).resolve():
        raise RuntimeError(
            f"Expected installed package {expected}, got {kaiserlift.__file__}"
        )
