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
        config={"displayModeBar": True, "displaylogo": False},
    )

    return (
        f'<div id="fig-{slug}-wrapper" class="{css_class}" '
        f'style="display:{display};">'
        f"{plotly_html}"
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
