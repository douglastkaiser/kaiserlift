"""Running data pipeline for KaiserLift.

This module provides the main entry point for processing running data
and generating interactive HTML output.
"""

from __future__ import annotations

from typing import IO, Iterable

from .running_processers import (
    highest_pace_per_distance,
    process_running_csv_files,
    df_next_running_targets,
)
from .running_viewers import gen_running_html_viewer


def running_pipeline(files: Iterable[IO], *, embed_assets: bool = True) -> str:
    """Process running data and return interactive HTML.

    This is the main entry point for processing running/cardio data.
    It loads CSV files, extracts Pareto front records, generates targets,
    and produces an interactive HTML visualization.

    Parameters
    ----------
    files:
        Iterable of file paths or file-like objects containing running CSV data.
        CSV should have columns: Date, Exercise, Category, Distance, Pace
    embed_assets:
        If True (default), return standalone HTML with embedded CSS/JS.
        If False, return fragment only (for embedding in existing pages).

    Returns
    -------
    str
        HTML output for running data visualization with:
        - Interactive table of target paces
        - Dropdown to filter by exercise
        - Plots showing Pareto front and targets
        - Dark mode support

    Examples
    --------
    >>> from kaiserlift import running_pipeline
    >>> html = running_pipeline(['running_data.csv'])
    >>> with open('running_output.html', 'w') as f:
    ...     f.write(html)
    """

    # Load & parse running CSV
    df = process_running_csv_files(files)

    # Extract records (Pareto front)
    records = highest_pace_per_distance(df)

    # Generate targets (validates pipeline)
    _ = df_next_running_targets(records)

    # Generate HTML
    return gen_running_html_viewer(df, embed_assets=embed_assets)
