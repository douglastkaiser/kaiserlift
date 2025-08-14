"""High-level data processing pipeline for KaiserLift.

The pipeline centralizes all numeric calculations in Python. Client-side
JavaScript is limited to user interface updates such as filtering or
showing figures and does not duplicate these computations.
"""

from __future__ import annotations

import sys
from typing import IO, Iterable

from .df_processers import (
    df_next_pareto,
    highest_weight_per_rep,
    process_csv_files,
)
from .viewers import gen_html_viewer


def pipeline(files: Iterable[IO], *, embed_assets: bool | None = None) -> str:
    """Run the KaiserLift processing pipeline and return HTML.

    Parameters
    ----------
    files:
        Iterable of file paths or file-like objects containing FitNotes CSV data.
    embed_assets:
        When ``True`` include ``<script>`` and ``<link>`` tags in the returned
        HTML. If ``None`` (the default), assets are embedded unless the code is
        executing in a Pyodide environment.

    Returns
    -------
    str
        The HTML output produced by :func:`gen_html_viewer`.

    Notes
    -----
    All heavy computations happen here on the server. The JavaScript emitted in
    the HTML focuses solely on updating the UI and performs no calculations.
    """

    df = process_csv_files(files)

    # Execute full pipeline for side effects and potential validation.
    records = highest_weight_per_rep(df)
    _ = df_next_pareto(records)

    if embed_assets is None:
        embed_assets = sys.platform != "emscripten"

    return gen_html_viewer(df, embed_assets=embed_assets)
