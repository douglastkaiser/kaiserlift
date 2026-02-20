"""Shared plotting utilities for KaiserLift visualizations."""

import re

import numpy as np
import pandas as pd


def dates_to_marker_props(dates) -> dict:
    """Map a sequence of dates to Plotly marker properties with a date-based colorscale.

    Recent PRs are shown in saturated dark red; older PRs fade toward light salmon.
    When only a single date is present, all markers are solid red.

    Parameters
    ----------
    dates : sequence of datetime-like
        One date per Pareto point, in the same order as the marker coordinates.

    Returns
    -------
    dict
        Keyword dict suitable for ``go.Scatter(marker=...)``.
    """
    ts = pd.to_datetime(dates)
    n = len(ts)

    if n == 0:
        return dict(color="red", size=10, symbol="circle")

    if n == 1 or ts.min() == ts.max():
        return dict(color="red", size=10, symbol="circle")

    # Map dates to 0..1 (oldest=0, newest=1)
    day_nums = np.array([(d - ts.min()).days for d in ts], dtype=float)
    day_nums /= day_nums.max()

    # Build colorbar tick marks (up to 5 evenly-spaced dates)
    n_ticks = min(5, n)
    tick_positions = np.linspace(0, 1, n_ticks)
    tick_dates = pd.to_datetime(
        [ts.min() + (ts.max() - ts.min()) * p for p in tick_positions]
    )
    tick_labels = [d.strftime("%Y-%m-%d") for d in tick_dates]

    return dict(
        color=day_nums.tolist(),
        colorscale=[
            [0, "rgba(255, 180, 160, 0.8)"],
            [0.5, "rgba(230, 80, 50, 0.9)"],
            [1, "rgba(180, 20, 10, 1)"],
        ],
        size=10,
        symbol="circle",
        colorbar=dict(
            title=dict(text="Date", font=dict(size=11)),
            tickvals=tick_positions.tolist(),
            ticktext=tick_labels,
            len=0.5,
            thickness=12,
            x=1.02,
        ),
        line=dict(color="darkred", width=0.5),
    )


def slugify(name: str) -> str:
    """Return a normalized slug for the given exercise name.

    Parameters
    ----------
    name : str
        Exercise name to slugify

    Returns
    -------
    str
        Slugified name suitable for HTML IDs
    """
    slug = re.sub(r"[^\w]+", "_", name)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug.lower()


def plotly_figure_to_html_div(
    fig, slug: str, display: str = "none", css_class: str = "exercise-figure"
) -> str:
    """Convert a Plotly figure to an HTML div with wrapper.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to convert
    slug : str
        Slugified name for the div ID
    display : str, optional
        CSS display property value (default: "none")
    css_class : str, optional
        CSS class for the wrapper div (default: "exercise-figure")

    Returns
    -------
    str
        HTML string with Plotly div wrapped in a container
    """
    plotly_html = fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        div_id=f"fig-{slug}",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "responsive": True,
        },
    )

    return (
        f'<div id="fig-{slug}-wrapper" class="{css_class}" '
        f'style="display:{display};">'
        f"{plotly_html}"
        f"</div>"
    )


def plotly_figures_pair_to_html_div(
    fig1, fig2, slug: str, display: str = "none", css_class: str = "exercise-figure"
) -> str:
    """Wrap two Plotly figures vertically inside a single container div.

    The outer div carries the ``id`` and ``css_class`` used for JS show/hide,
    so both figures are toggled together as one unit.

    Parameters
    ----------
    fig1 : plotly.graph_objects.Figure
        First (top) figure.
    fig2 : plotly.graph_objects.Figure
        Second (bottom) figure.
    slug : str
        Slugified name; outer id becomes ``fig-{slug}-wrapper`` and the two
        inner Plotly divs get ids ``fig-{slug}`` and ``fig-{slug}-secondary``.
    display : str, optional
        CSS display property for the outer wrapper (default: ``"none"``).
    css_class : str, optional
        CSS class for the outer wrapper (default: ``"exercise-figure"``).

    Returns
    -------
    str
        HTML string with both Plotly divs inside a single container.
    """
    config = {"displayModeBar": True, "displaylogo": False, "responsive": True}

    html1 = fig1.to_html(
        include_plotlyjs=False,
        full_html=False,
        div_id=f"fig-{slug}",
        config=config,
    )
    html2 = fig2.to_html(
        include_plotlyjs=False,
        full_html=False,
        div_id=f"fig-{slug}-secondary",
        config=config,
    )

    return (
        f'<div id="fig-{slug}-wrapper" class="{css_class}" style="display:{display};">'
        f'<div style="width:100%;overflow:hidden;margin-bottom:15px;">{html1}</div>'
        f'<div style="width:100%;overflow:hidden;">{html2}</div>'
        f"</div>"
    )


def get_plotly_cdn_html() -> str:
    """Return HTML for loading Plotly.js from CDN.

    Returns
    -------
    str
        HTML script tags for Plotly
    """
    return """
    <!-- Plotly for interactive plots -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>"""


def get_plotly_preconnect_html() -> str:
    """Return HTML preconnect tag for Plotly CDN.

    Returns
    -------
    str
        HTML preconnect link tag
    """
    return '<link rel="preconnect" href="https://cdn.plot.ly">'
