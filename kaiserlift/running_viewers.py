"""Running data visualization module for KaiserLift.

This module provides plotting and HTML generation functionality for
running/cardio data visualization.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from .running_processers import (
    estimate_pace_at_distance,
    highest_pace_per_distance,
    df_next_running_targets,
    seconds_to_pace_string,
    add_speed_metric_column,
)
from .plot_utils import (
    slugify,
    plotly_figure_to_html_div,
    get_plotly_cdn_html,
    get_plotly_preconnect_html,
)


def plot_running_df(df_pareto=None, df_targets=None, Exercise: str = None):
    """Plot running performance: Distance vs Speed.

    Similar to plot_df for lifting but with running metrics:
    - X-axis: Distance (miles)
    - Y-axis: Speed (mph, higher is better)
    - Red line: Pareto front of best speeds
    - Green X: Target speeds to achieve

    Parameters
    ----------
    df_pareto : pd.DataFrame, optional
        Pareto front records
    df_targets : pd.DataFrame, optional
        Target running goals
    Exercise : str, optional
        Specific exercise to plot. Must be specified.

    Returns
    -------
    plotly.graph_objects.Figure
        The generated interactive figure
    """

    if df_pareto is None or df_pareto.empty:
        raise ValueError("df_pareto must be provided and non-empty")

    if Exercise is None:
        raise ValueError("Exercise must be specified")

    # Add Speed to pareto and targets if needed
    if df_pareto is not None:
        df_pareto = df_pareto[df_pareto["Exercise"] == Exercise].copy()
        if "Speed" not in df_pareto.columns and "Pace" in df_pareto.columns:
            df_pareto["Speed"] = df_pareto["Pace"].apply(
                lambda p: 3600 / p if pd.notna(p) and p > 0 else np.nan
            )

    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == Exercise].copy()
        if "Speed" not in df_targets.columns and "Pace" in df_targets.columns:
            df_targets["Speed"] = df_targets["Pace"].apply(
                lambda p: 3600 / p if pd.notna(p) and p > 0 else np.nan
            )

    # Calculate axis limits
    distance_series = [df_pareto["Distance"]]
    if df_targets is not None and not df_targets.empty:
        distance_series.append(df_targets["Distance"])

    min_dist = min(s.min() for s in distance_series)
    max_dist = max(s.max() for s in distance_series)
    plot_max_dist = max_dist + 1

    fig = go.Figure()

    # Initialize pareto curve parameters
    best_pace = np.nan
    best_distance = np.nan

    # Plot Pareto front (red line)
    if df_pareto is not None and not df_pareto.empty:
        pareto_points = list(zip(df_pareto["Distance"], df_pareto["Speed"]))
        pareto_dists, pareto_speeds = zip(*sorted(pareto_points, key=lambda x: x[0]))

        # Compute best speed overall (maximum)
        max_speed = max(pareto_speeds)

        # Get the pace corresponding to max_speed for curve estimation
        max_speed_idx = pareto_speeds.index(max_speed)
        best_pace = 3600 / max_speed if max_speed > 0 else np.nan
        best_distance = pareto_dists[max_speed_idx]

        # Generate speed curve (convert pace estimates to speed)
        if not np.isnan(best_pace):
            x_vals = np.linspace(min_dist, plot_max_dist, 100).tolist()
            x_vals.append(float(best_distance))
            x_vals = sorted(set(x_vals))

            y_vals = []
            for d in x_vals:
                pace_est = estimate_pace_at_distance(best_pace, best_distance, d)
                if pace_est > 0 and not np.isnan(pace_est):
                    y_vals.append(3600 / pace_est)
                else:
                    y_vals.append(np.nan)

            # Ensure the curve intersects the Pareto point with best speed
            anchor_idx = x_vals.index(best_distance)
            y_vals[anchor_idx] = max_speed

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Best Speed Curve",
                    line=dict(color="black", dash="dash", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Best Speed Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Speed: %{y:.2f} mph<br>"
                    + f"Pace: {seconds_to_pace_string(best_pace)}<extra></extra>",
                )
            )

        # Plot step line
        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_speeds),
                mode="lines",
                name="Pareto Front (Best Speeds)",
                line=dict(color="red", shape="hv", width=2),
                hovertemplate="<b>Pareto Front</b><extra></extra>",
            )
        )

        # Plot markers
        pareto_paces = [
            seconds_to_pace_string(3600 / s) if s > 0 else "N/A" for s in pareto_speeds
        ]
        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_speeds),
                mode="markers",
                name="Pareto Points",
                marker=dict(color="red", size=10, symbol="circle"),
                hovertemplate="<b>Pareto Point</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Speed: %{y:.2f} mph<br>"
                + "Pace: %{customdata}<extra></extra>",
                customdata=pareto_paces,
                showlegend=False,
            )
        )

    # Plot targets (green X)
    if df_targets is not None and not df_targets.empty:
        target_points = list(zip(df_targets["Distance"], df_targets["Speed"]))
        target_dists, target_speeds = zip(*sorted(target_points, key=lambda x: x[0]))

        # Find the target furthest below the pareto curve (easiest to achieve)
        if not np.isnan(best_pace):
            # Find target with maximum distance below pareto curve
            max_distance_below_pareto = -float("inf")
            furthest_below_idx = 0

            for i, (t_dist, t_speed) in enumerate(zip(target_dists, target_speeds)):
                # Estimate pareto speed at this target distance
                pareto_pace_est = estimate_pace_at_distance(
                    best_pace, best_distance, t_dist
                )
                if not np.isnan(pareto_pace_est) and pareto_pace_est > 0:
                    pareto_speed_est = 3600 / pareto_pace_est
                    # Calculate how far below the pareto curve this target is
                    # Positive value means target is below pareto (easier to achieve)
                    distance_below = pareto_speed_est - t_speed
                    if distance_below > max_distance_below_pareto:
                        max_distance_below_pareto = distance_below
                        furthest_below_idx = i

            target_pace = (
                3600 / target_speeds[furthest_below_idx]
                if target_speeds[furthest_below_idx] > 0
                else np.nan
            )
            target_distance = target_dists[furthest_below_idx]
        else:
            # Fallback: use max speed (original behavior)
            max_target_speed = max(target_speeds)
            max_target_idx = target_speeds.index(max_target_speed)
            target_pace = 3600 / max_target_speed if max_target_speed > 0 else np.nan
            target_distance = target_dists[max_target_idx]

        # Generate dotted target speed curve
        if not np.isnan(target_pace):
            x_vals = np.linspace(min_dist, plot_max_dist, 100).tolist()
            x_vals.append(float(target_distance))
            x_vals = sorted(set(x_vals))

            y_vals = []
            for d in x_vals:
                pace_est = estimate_pace_at_distance(target_pace, target_distance, d)
                if pace_est > 0 and not np.isnan(pace_est):
                    y_vals.append(3600 / pace_est)
                else:
                    y_vals.append(np.nan)

            # Ensure target speed curve intersects chosen target
            anchor_idx = x_vals.index(target_distance)
            y_vals[anchor_idx] = target_speeds[furthest_below_idx]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Target Speed Curve",
                    line=dict(color="green", dash="dashdot", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Target Speed Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Speed: %{y:.2f} mph<br>"
                    + f"Pace: {seconds_to_pace_string(target_pace)}<extra></extra>",
                )
            )

        # Target markers
        target_paces = [
            seconds_to_pace_string(3600 / s) if s > 0 else "N/A" for s in target_speeds
        ]
        fig.add_trace(
            go.Scatter(
                x=list(target_dists),
                y=list(target_speeds),
                mode="markers",
                name="Next Targets",
                marker=dict(color="green", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Speed: %{y:.2f} mph<br>"
                + "Pace: %{customdata}<extra></extra>",
                customdata=target_paces,
            )
        )

    fig.update_layout(
        title=f"Speed vs. Distance for {Exercise}",
        xaxis_title="Distance (miles)",
        yaxis_title="Speed (mph, higher=faster)",
        xaxis_type="log",
        xaxis=dict(range=[np.log10(min_dist * 0.9), np.log10(plot_max_dist)]),
        hovermode="closest",
        template="plotly_white",
    )

    return fig


def render_running_table_fragment(df) -> str:
    """Render HTML fragment with running data visualization.

    Parameters
    ----------
    df : pd.DataFrame
        Running data

    Returns
    -------
    str
        HTML fragment with dropdown, table, and figures
    """

    df_records = highest_pace_per_distance(df)
    # Ensure df_records has Speed column for distance calculations
    df_records = add_speed_metric_column(df_records)
    df_targets = df_next_running_targets(df_records)

    # Format pace columns for display
    if not df_targets.empty:
        df_targets_display = df_targets.copy()

        # Calculate distance from pareto curve for each target
        distances_from_pareto = []
        for _, row in df_targets_display.iterrows():
            exercise = row["Exercise"]
            target_dist = row["Distance"]
            target_speed = row["Speed"]

            # Get pareto data for this exercise
            exercise_records = df_records[df_records["Exercise"] == exercise]
            if not exercise_records.empty:
                # Find best speed on pareto front
                pareto_speeds = exercise_records["Speed"].tolist()
                pareto_dists = exercise_records["Distance"].tolist()
                max_speed = max(pareto_speeds)
                max_speed_idx = pareto_speeds.index(max_speed)
                best_pace = 3600 / max_speed if max_speed > 0 else np.nan
                best_distance = pareto_dists[max_speed_idx]

                # Estimate pareto speed at target distance
                if not np.isnan(best_pace):
                    pareto_pace_est = estimate_pace_at_distance(
                        best_pace, best_distance, target_dist
                    )
                    if not np.isnan(pareto_pace_est) and pareto_pace_est > 0:
                        pareto_speed_est = 3600 / pareto_pace_est
                        # Calculate how far below the pareto curve this target is
                        # Positive = target below pareto (easier to achieve)
                        # Negative = target above pareto (already exceeded)
                        distance_below = pareto_speed_est - target_speed
                        distances_from_pareto.append(distance_below)
                    else:
                        distances_from_pareto.append(-np.inf)
                else:
                    distances_from_pareto.append(-np.inf)
            else:
                distances_from_pareto.append(-np.inf)

        df_targets_display["Distance Below Pareto (mph)"] = distances_from_pareto
        df_targets_display["Distance Below Pareto (mph)"] = df_targets_display[
            "Distance Below Pareto (mph)"
        ].round(3)

        df_targets_display["Pace"] = df_targets_display["Pace"].apply(
            seconds_to_pace_string
        )
        df_targets_display["Speed"] = df_targets_display["Speed"].round(2)
    else:
        df_targets_display = df_targets

    figures_html: dict[str, str] = {}

    exercise_slug = {ex: slugify(ex) for ex in df_records["Exercise"].unique()}

    # Generate plots for each exercise
    for exercise, slug in exercise_slug.items():
        try:
            fig = plot_running_df(df_records, df_targets, Exercise=exercise)
            # Convert Plotly figure to HTML div with wrapper
            img_html = plotly_figure_to_html_div(
                fig, slug, display="block", css_class="running-figure"
            )
            figures_html[exercise] = img_html
        except Exception:
            # If plot generation fails, skip this exercise and continue
            plt.close("all")  # Clean up any partial figures

    all_figures_html = "\n".join(figures_html.values())

    # Convert targets to table
    table_html = df_targets_display.to_html(
        classes="display compact cell-border", table_id="runningTable", index=False
    )

    return table_html + all_figures_html


def gen_running_html_viewer(df, *, embed_assets: bool = True) -> str:
    """Generate full HTML viewer for running data.

    Parameters
    ----------
    df : pd.DataFrame
        Running data
    embed_assets : bool
        If True (default), return standalone HTML. If False, return fragment only.

    Returns
    -------
    str
        Complete HTML page or fragment
    """

    fragment = render_running_table_fragment(df)

    if not embed_assets:
        return fragment

    # Include same CSS/JS as lifting viewer
    js_and_css = (
        """
    <!-- Preconnect to CDNs for faster loading -->
    <link rel="preconnect" href="https://code.jquery.com">
    <link rel="preconnect" href="https://cdn.datatables.net">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;700&family=Lato:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap" rel="stylesheet">
    """
        + get_plotly_preconnect_html()
        + "\n"
        + get_plotly_cdn_html()
        + """

    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js" defer></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js" defer></script>

    <!-- Custom Styling -->
    <style>
    :root {
        --primary-green: #4a7c59;
        --primary-green-hover: #3d6a4a;
        --bg: #f9f9f9;
        --fg: #444444;
        --fg-light: #666666;
        --bg-alt: #ffffff;
        --border: #e0e0e0;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --link: #4a7c59;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Lato', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 16px;
        padding: 30px;
        background-color: var(--bg);
        color: var(--fg);
        line-height: 1.6;
        max-width: 1400px;
        margin: 0 auto;
    }

    h1, h2, h3 {
        font-family: 'Oswald', sans-serif;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .page-header {
        text-align: center;
        margin-bottom: 40px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }

    .page-header h1 {
        font-size: 2.5em;
        margin-bottom: 10px;
    }

    .page-header h1 .brand-name {
        color: var(--fg);
    }

    .page-header h1 .brand-accent {
        color: var(--primary-green);
    }

    .page-header .subtitle {
        font-style: italic;
        font-weight: 300;
        color: var(--fg-light);
    }

    /* Table wrapper for horizontal scrolling on mobile */
    .table-wrapper {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-bottom: 16px;
    }

    table.dataTable {
        font-size: 14px;
        width: 100% !important;
        min-width: 500px;
        word-wrap: break-word;
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: 4px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }

    table.dataTable thead th {
        background-color: var(--primary-green);
        color: white;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 0.5px;
        padding: 12px 10px;
        border-bottom: none;
        white-space: nowrap;
    }

    table.dataTable tbody td {
        padding: 10px;
        border-bottom: 1px solid var(--border);
    }

    table.dataTable tbody tr:hover {
        background-color: rgba(74, 124, 89, 0.05);
    }

    table.dataTable tbody tr:nth-child(even) {
        background-color: rgba(0, 0, 0, 0.02);
    }

    /* DataTables controls styling */
    .dataTables_wrapper {
        font-size: 14px;
    }

    .dataTables_wrapper .dataTables_length,
    .dataTables_wrapper .dataTables_filter {
        margin-bottom: 15px;
    }

    .dataTables_wrapper .dataTables_filter input {
        font-family: 'Lato', sans-serif;
        font-size: 14px;
        padding: 8px 12px;
        border-radius: 4px;
        border: 1px solid var(--border);
        background-color: var(--bg-alt);
        color: var(--fg);
        min-height: 40px;
    }

    .dataTables_wrapper .dataTables_filter input:focus {
        outline: none;
        border-color: var(--primary-green);
        box-shadow: 0 0 0 2px rgba(74, 124, 89, 0.1);
    }

    .dataTables_wrapper .dataTables_length select {
        font-family: 'Lato', sans-serif;
        font-size: 14px;
        padding: 8px;
        border-radius: 4px;
        border: 1px solid var(--border);
        background-color: var(--bg-alt);
        color: var(--fg);
        min-height: 40px;
    }

    .dataTables_wrapper .dataTables_paginate {
        margin-top: 15px;
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }

    .dataTables_wrapper .dataTables_paginate .paginate_button {
        padding: 8px 12px !important;
        min-width: 40px;
        min-height: 40px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        font-size: 14px;
        background-color: var(--bg-alt) !important;
        border: 1px solid var(--border) !important;
        color: var(--fg) !important;
        transition: all 0.2s ease;
    }

    .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
        background-color: var(--primary-green) !important;
        color: white !important;
        border-color: var(--primary-green) !important;
    }

    .dataTables_wrapper .dataTables_paginate .paginate_button.current {
        background-color: var(--primary-green) !important;
        color: white !important;
        border-color: var(--primary-green) !important;
    }

    .dataTables_wrapper .dataTables_info {
        font-size: 13px;
        padding-top: 15px;
        color: var(--fg-light);
    }

    label {
        font-family: 'Lato', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: var(--fg);
        margin-bottom: 8px;
        display: inline-block;
    }

    select {
        font-family: 'Lato', sans-serif;
        font-size: 14px;
        color: var(--fg);
        background-color: var(--bg-alt);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 10px 12px;
        min-height: 40px;
    }

    select:focus {
        outline: none;
        border-color: var(--primary-green);
        box-shadow: 0 0 0 2px rgba(74, 124, 89, 0.1);
    }

    .upload-controls {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        margin-bottom: 25px;
        padding: 20px;
        background-color: var(--bg-alt);
        border: 1px solid var(--border);
        border-radius: 4px;
    }

    #uploadButton {
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        background-color: var(--primary-green);
        color: white;
        cursor: pointer;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
        min-height: 40px;
        white-space: nowrap;
    }

    #uploadButton:hover {
        background-color: var(--primary-green-hover);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    #uploadButton:active {
        transform: translateY(0);
    }

    #csvFile {
        padding: 8px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background-color: var(--bg);
        color: var(--fg);
        font-family: 'Lato', sans-serif;
        font-size: 14px;
        min-height: 40px;
        max-width: 100%;
    }

    #csvFile:focus {
        outline: none;
        border-color: var(--primary-green);
    }

    #uploadProgress {
        flex: 1;
        min-width: 100px;
    }

    /* Back link styling */
    .back-link {
        display: inline-block;
        margin-bottom: 20px;
        color: var(--primary-green);
        text-decoration: none;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.9em;
        letter-spacing: 1px;
    }

    .back-link:hover {
        text-decoration: underline;
    }

    /* Chart container styling */
    .running-figure {
        border-radius: 4px;
        box-shadow: var(--shadow);
        margin: 25px 0;
        opacity: 0;
        animation: fadeIn 0.3s ease-in forwards;
        width: 100%;
        overflow: hidden;
        background-color: var(--bg-alt);
    }

    .running-figure .js-plotly-plot,
    .running-figure .plotly {
        width: 100% !important;
    }

    .running-figure .main-svg {
        width: 100% !important;
        height: auto !important;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .running-figure svg {
        max-width: 100%;
        height: auto;
        display: block;
    }

    /* Tablet breakpoint */
    @media only screen and (max-width: 768px) {
        body {
            padding: 20px 15px;
        }

        .page-header h1 {
            font-size: 2em;
        }

        .upload-controls {
            flex-direction: column;
            align-items: stretch;
        }

        #csvFile {
            width: 100%;
        }

        #uploadButton {
            width: 100%;
            text-align: center;
        }

        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_filter {
            float: none;
            text-align: left;
            width: 100%;
        }

        .dataTables_wrapper .dataTables_filter input {
            width: 100%;
            margin-left: 0;
            margin-top: 8px;
        }
    }

    /* Mobile breakpoint */
    @media only screen and (max-width: 480px) {
        body {
            padding: 15px 10px;
        }

        .page-header h1 {
            font-size: 1.75em;
        }

        .dataTables_wrapper .dataTables_paginate .paginate_button {
            padding: 6px 10px !important;
            min-width: 36px;
            font-size: 13px;
        }

        .dataTables_wrapper .dataTables_info {
            text-align: center;
            width: 100%;
        }

        .dataTables_wrapper .dataTables_paginate {
            justify-content: center;
            width: 100%;
        }
    }
    </style>
    """
    )

    upload_html = """
    <a href="/" class="back-link">&larr; Back to Home</a>
    <div class="page-header">
        <h1><span class="brand-name">KAISER</span><span class="brand-accent">LIFT</span></h1>
        <p class="subtitle">Running Data Analysis</p>
    </div>
    <div class="upload-controls">
        <input type="file" id="csvFile" accept=".csv">
        <button id="uploadButton">Upload</button>
        <progress id="uploadProgress" value="0" max="100" style="display:none;"></progress>
    </div>
    """

    scripts = """
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script>
    $(document).ready(function() {
        // Initialize DataTable
        $('#runningTable').DataTable({
            pageLength: 25,
            order: [[4, 'desc']]  // Sort by "Distance Below Pareto" column (index 4) - easiest targets first
        });
    });
    </script>
    """

    meta = """
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="description" content="KaiserLift running analysis - Data-driven pace optimization with Pareto front">
    """
    version_footer = """
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 0.85em; color: var(--fg-light); text-align: center;">
        <span id="version-info">Loading version...</span>
        <span style="margin: 0 10px;">|</span>
        <a href="https://douglastkaiser.github.io" target="_blank" style="color: var(--primary-green); text-decoration: none;">douglastkaiser.github.io</a>
    </footer>
    <script type="module">
        import { VERSION, GIT_HASH, GIT_HASH_FULL } from '../version.js';
        const versionEl = document.getElementById('version-info');
        const commitUrl = `https://github.com/douglastkaiser/kaiserlift/commit/${GIT_HASH_FULL}`;
        versionEl.innerHTML = `v${VERSION} (<a href="${commitUrl}" target="_blank" style="color: var(--primary-green);">${GIT_HASH}</a>)`;
    </script>
    """
    body_html = upload_html + f'<div id="result">{fragment}</div>' + version_footer
    return (
        f"<html><head>{meta}{js_and_css}</head><body>{body_html}{scripts}</body></html>"
    )
