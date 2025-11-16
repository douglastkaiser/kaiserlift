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
            x_vals = np.linspace(min_dist, plot_max_dist, 100)
            y_vals = []
            for d in x_vals:
                pace_est = estimate_pace_at_distance(best_pace, best_distance, d)
                if pace_est > 0 and not np.isnan(pace_est):
                    y_vals.append(3600 / pace_est)
                else:
                    y_vals.append(np.nan)
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
            x_vals = np.linspace(min_dist, plot_max_dist, 100)
            y_vals = []
            for d in x_vals:
                pace_est = estimate_pace_at_distance(target_pace, target_distance, d)
                if pace_est > 0 and not np.isnan(pace_est):
                    y_vals.append(3600 / pace_est)
                else:
                    y_vals.append(np.nan)
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
    """
        + get_plotly_preconnect_html()
        + "\n"
        + get_plotly_cdn_html()
        + """

    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js" defer></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js" defer></script>

    <!-- Custom Styling for Mobile -->
    <style>
    :root {
        --bg: #fafafa;
        --fg: #1a1a1a;
        --bg-alt: #ffffff;
        --border: #e5e7eb;
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --success: #10b981;
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg: #0f0f0f;
            --fg: #e5e5e5;
            --bg-alt: #1a1a1a;
            --border: #2a2a2a;
            --primary: #60a5fa;
            --primary-hover: #3b82f6;
            --success: #34d399;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.3);
        }
    }
    [data-theme="dark"] {
        --bg: #0f0f0f;
        --fg: #e5e5e5;
        --bg-alt: #1a1a1a;
        --border: #2a2a2a;
        --primary: #60a5fa;
        --primary-hover: #3b82f6;
        --success: #34d399;
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.3);
    }
    [data-theme="light"] {
        --bg: #fafafa;
        --fg: #1a1a1a;
        --bg-alt: #ffffff;
        --border: #e5e7eb;
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --success: #10b981;
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }

    * {
        transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 34px;
        padding: 28px;
        background-color: var(--bg);
        color: var(--fg);
        line-height: 1.5;
    }

    h1 {
        font-weight: 700;
        margin-bottom: 24px;
    }

    table.dataTable {
        font-size: 32px;
        width: 100% !important;
        word-wrap: break-word;
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }

    table.dataTable thead th {
        background-color: var(--bg);
        font-weight: 600;
        padding: 12px;
        border-bottom: 2px solid var(--border);
    }

    table.dataTable tbody td {
        padding: 10px 12px;
    }

    table.dataTable tbody tr {
        border-bottom: 1px solid var(--border);
    }

    table.dataTable tbody tr:hover {
        background-color: var(--bg);
    }

    label {
        font-size: 34px;
        color: var(--fg);
        font-weight: 500;
        margin-bottom: 8px;
        display: inline-block;
    }

    select {
        font-size: 34px;
        color: var(--fg);
        background-color: var(--bg-alt);
        border: 2px solid var(--border);
        border-radius: 6px;
        padding: 8px 12px;
    }

    select:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* Dark mode overrides for DataTables and Select2 */
    @media (prefers-color-scheme: dark) {
        .dataTables_wrapper .dataTables_filter input,
        .dataTables_wrapper .dataTables_length select {
            background-color: var(--bg);
            color: var(--fg);
            border: 1px solid var(--border);
        }
        .dataTables_wrapper .dataTables_paginate .paginate_button {
            background-color: var(--bg);
            color: var(--fg) !important;
            border: 1px solid var(--border);
        }
        .dataTables_wrapper .dataTables_paginate .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
            background-color: var(--bg-alt) !important;
            color: var(--fg) !important;
        }
    }
    html[data-theme="dark"] .dataTables_wrapper .dataTables_filter input,
    html[data-theme="dark"] .dataTables_wrapper .dataTables_length select {
        background-color: var(--bg);
        color: var(--fg);
        border: 1px solid var(--border);
    }
    html[data-theme="dark"] .dataTables_wrapper .dataTables_paginate .paginate_button {
        background-color: var(--bg);
        color: var(--fg) !important;
        border: 1px solid var(--border);
    }
    html[data-theme="dark"] .dataTables_wrapper .dataTables_paginate .paginate_button.current,
    html[data-theme="dark"] .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
        background-color: var(--bg-alt) !important;
        color: var(--fg) !important;
    }

    .upload-controls {
        display: flex;
        gap: 12px;
        align-items: center;
        margin-bottom: 16px;
    }

    #uploadButton {
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        background-color: var(--primary);
        color: #ffffff;
        cursor: pointer;
        font-weight: 600;
        font-size: 28px;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }

    #uploadButton:hover {
        background-color: var(--primary-hover);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }

    #uploadButton:active {
        transform: translateY(0);
    }

    #csvFile {
        padding: 10px;
        border: 2px solid var(--border);
        border-radius: 6px;
        background-color: var(--bg-alt);
        color: var(--fg);
        font-size: 28px;
    }

    #csvFile:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    #uploadProgress {
        flex: 1;
    }

    .theme-toggle {
        position: fixed;
        top: 16px;
        right: 16px;
        padding: 10px 14px;
        font-size: 24px;
        cursor: pointer;
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 2px solid var(--border);
        border-radius: 8px;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
        z-index: 1000;
    }

    .theme-toggle:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }

    .running-figure {
        border-radius: 8px;
        box-shadow: var(--shadow);
        margin: 20px 0;
        opacity: 0;
        animation: fadeIn 0.3s ease-in forwards;
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

    @media only screen and (max-width: 600px) {
        body {
            padding: 16px;
        }

        h1 {
            font-size: 2em;
        }

        table.dataTable {
            font-size: 28px;
        }

        label {
            font-size: 30px;
        }

        select {
            font-size: 30px;
        }

        #uploadButton {
            font-size: 26px;
            padding: 12px 20px;
        }

        #csvFile {
            font-size: 26px;
        }

        .upload-controls {
            flex-direction: column;
            align-items: stretch;
        }
    }
    </style>
    """
    )

    upload_html = """
    <button class="theme-toggle" id="themeToggle">🌙</button>
    <h1>KaiserLift - Running Data</h1>
    <div class="upload-controls">
        <input type="file" id="csvFile" accept=".csv">
        <button id="uploadButton">Upload Running Data</button>
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

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';

        themeToggle.addEventListener('click', function() {
            const theme = document.documentElement.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    });
    </script>
    """

    meta = """
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="description" content="KaiserLift running analysis - Data-driven pace optimization with Pareto front">
    """
    body_html = upload_html + f'<div id="result">{fragment}</div>'
    return (
        f"<html><head>{meta}{js_and_css}</head><body>{body_html}{scripts}</body></html>"
    )
