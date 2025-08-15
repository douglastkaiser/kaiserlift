"""High-level data processing pipeline for KaiserLift.

The pipeline centralizes all numeric calculations in Python. Client-side
JavaScript is limited to user interface updates such as filtering or
showing figures and does not duplicate these computations.
"""

from __future__ import annotations

from typing import IO, Iterable

from .df_processers import (
    df_next_pareto,
    highest_weight_per_rep,
    process_csv_files,
)
from .viewers import gen_html_viewer


def pipeline(files: Iterable[IO], *, embed_assets: bool = True) -> str:
    """Run the KaiserLift processing pipeline and return HTML.

    Parameters
    ----------
    files:
        Iterable of file paths or file-like objects containing FitNotes CSV
        data.
    embed_assets:
        If ``True`` (default) the returned HTML includes the upload controls and
        required CSS/JavaScript for a standalone page. Set to ``False`` to
        obtain only the table/dropdown/figure fragment suitable for insertion
        into an existing ``<div id="result">`` where the surrounding page
        already provides the necessary assets.

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

    return gen_html_viewer(df, embed_assets=embed_assets)
