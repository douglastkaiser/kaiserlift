"""High-level data processing pipeline for KaiserLift.

The pipeline centralizes all numeric calculations in Python. Client-side
JavaScript is limited to user interface updates such as filtering or
showing figures and does not duplicate these computations.
"""

from __future__ import annotations

from pathlib import Path
from typing import IO, Iterable

from .df_processers import (
    df_next_pareto,
    highest_weight_per_rep,
    process_csv_files,
)
from .viewers import gen_html_viewer


def pipeline(files: Iterable[IO], *, embed_assets: bool = False) -> str:
    """Run the KaiserLift processing pipeline and return HTML.

    Parameters
    ----------
    files:
        Iterable of file paths or file-like objects containing FitNotes CSV data.

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

    html = gen_html_viewer(df)
    if embed_assets:
        main_js = Path(__file__).resolve().parent.parent / "client" / "main.js"
        if main_js.exists():
            script = main_js.read_text(encoding="utf-8")
            html = html.replace(
                '<script type="module" src="main.js"></script>',
                f'<script type="module">{script}</script>',
            )
        html = f"<!DOCTYPE html><html><head></head><body>{html}</body></html>"

    return html
