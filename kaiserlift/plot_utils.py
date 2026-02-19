"""Shared plotting utilities for KaiserLift visualizations."""

import re


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
