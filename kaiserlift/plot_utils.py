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


def apply_plot_theme(fig) -> None:
    """Apply the lab's instrument styling without altering any data or curves."""
    fig.update_layout(
        paper_bgcolor="#fffef8",
        plot_bgcolor="#fffef8",
        font=dict(family="Courier New, monospace", size=11, color="#171915"),
        hoverlabel=dict(
            bgcolor="#171915", font=dict(color="#f3f1e9", family="Courier New")
        ),
        legend=dict(
            bgcolor="#fffef8",
            bordercolor="#b7b9ab",
            borderwidth=1,
            font=dict(size=10),
            orientation="h",
            y=-0.18,
            x=0,
            xanchor="left",
        ),
    )
    if fig.layout.title and fig.layout.title.text:
        fig.update_layout(title=None, margin=dict(t=48))
    # Race-distance labels compete with subplot titles on narrow screens.
    fig.layout.annotations = tuple(
        annotation
        for annotation in fig.layout.annotations
        if annotation.text not in {"5K", "Half", "Marathon"}
    )
    for annotation in fig.layout.annotations or ():
        annotation.font.update(
            family="Courier New, monospace", size=12, color="#171915"
        )
    for axis_name in fig.layout:
        if axis_name.startswith(("xaxis", "yaxis")):
            axis = fig.layout[axis_name]
            if axis.type == "log" and axis.tickmode != "array":
                ticks = [0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 240, 600]
                axis.update(
                    tickmode="array", tickvals=ticks, ticktext=[str(t) for t in ticks]
                )
    fig.update_xaxes(
        gridcolor="#e0e2d5",
        zerolinecolor="#171915",
        linecolor="#171915",
        showline=True,
        ticks="outside",
        tickcolor="#171915",
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="#e0e2d5",
        zerolinecolor="#171915",
        linecolor="#171915",
        showline=True,
        ticks="outside",
        tickcolor="#171915",
        automargin=True,
    )
    for trace in fig.data:
        name = trace.name or ""
        if "Selected" in name:
            color = "#171915"
        elif "Recommended" in name:
            color = "#d04c26"
        elif "Target" in name or "target" in name:
            color = "#13795a"
        elif "Pareto" in name:
            color = "#2744da"
        else:
            color = "#64695b"
        if trace.type == "scatter":
            trace.line.color = color
            trace.marker.color = color


def plotly_figure_to_html_div(
    fig, slug: str, display: str = "none", css_class: str = "exercise-figure"
) -> str:
    """Convert a Plotly figure to a wrapper containing an inert JSON payload.

    Standalone viewers include the shared dashboard initializer. Call
    ``initializeDashboard(root)`` after inserting a fragment in the browser.

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
    # JSON payloads can be initialized after uploads and cache restoration without
    # evaluating inline scripts. Escape '<' so exercise names cannot close the tag.
    apply_plot_theme(fig)
    payload = fig.to_json().replace("<", "\\u003c")
    plotly_html = (
        f'<div id="fig-{slug}" class="plotly-graph-div" data-plot>'
        f'<script type="application/json">{payload}</script></div>'
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
