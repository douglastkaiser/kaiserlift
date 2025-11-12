"""Running data visualization module for KaiserLift.

This module provides plotting and HTML generation functionality for
running/cardio data visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

from .running_processers import (
    estimate_pace_at_distance,
    highest_pace_per_distance,
    df_next_running_targets,
    seconds_to_pace_string,
)


def plot_running_df(df, df_pareto=None, df_targets=None, Exercise: str = None):
    """Plot running performance: Distance vs Pace.

    Similar to plot_df for lifting but with running metrics:
    - X-axis: Distance (miles)
    - Y-axis: Pace (seconds/mile, lower is better)
    - Red line: Pareto front of best paces
    - Green X: Target paces to achieve

    Parameters
    ----------
    df : pd.DataFrame
        Full running data
    df_pareto : pd.DataFrame, optional
        Pareto front records
    df_targets : pd.DataFrame, optional
        Target running goals
    Exercise : str, optional
        Specific exercise to plot. If None, plots all exercises normalized.

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure
    """

    df = df[df["Distance"] > 0]

    if Exercise is None:
        # Plot all exercises normalized
        exercises = df["Exercise"].unique()
        fig, ax = plt.subplots()
        for exercise in exercises:
            ex_df = df[df["Exercise"] == exercise]
            ax.scatter(
                ex_df["Distance"] / max(ex_df["Distance"]),
                ex_df["Pace"] / max(ex_df["Pace"]),
                label=exercise,
                alpha=0.6,
            )
        ax.set_title("Pace vs. Distance for All Running Exercises")
        ax.set_xlabel("Distance (normalized)")
        ax.set_ylabel("Pace (normalized, lower=faster)")
        ax.legend()
        return fig

    # Filter to specific exercise
    df = df[df["Exercise"] == Exercise]
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"No data for {Exercise}", ha="center")
        return fig

    if df_pareto is not None:
        df_pareto = df_pareto[df_pareto["Exercise"] == Exercise]
    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == Exercise]

    # Calculate axis limits
    distance_series = [df["Distance"]]
    if df_pareto is not None and not df_pareto.empty:
        distance_series.append(df_pareto["Distance"])
    if df_targets is not None and not df_targets.empty:
        distance_series.append(df_targets["Distance"])

    min_dist = min(s.min() for s in distance_series)
    max_dist = max(s.max() for s in distance_series)
    plot_max_dist = max_dist + 1

    fig, ax = plt.subplots()

    # Plot Pareto front (red line)
    if df_pareto is not None and not df_pareto.empty:
        pareto_points = list(zip(df_pareto["Distance"], df_pareto["Pace"]))
        pareto_dists, pareto_paces = zip(*sorted(pareto_points, key=lambda x: x[0]))

        # Compute best pace overall
        min_pace = min(pareto_paces)

        # Generate pace degradation curve
        x_vals = np.linspace(min_dist, plot_max_dist, 100)
        y_vals = [
            estimate_pace_at_distance(min_pace, pareto_dists[0], d) for d in x_vals
        ]
        ax.plot(x_vals, y_vals, "k--", label="Best Pace Curve", alpha=0.7)

        # Plot step line and markers
        ax.step(
            pareto_dists,
            pareto_paces,
            color="red",
            label="Pareto Front (Best Paces)",
        )
        ax.scatter(
            pareto_dists,
            pareto_paces,
            color="red",
            marker="o",
            label="_nolegend_",
        )

    # Plot targets (green X)
    if df_targets is not None and not df_targets.empty:
        target_points = list(zip(df_targets["Distance"], df_targets["Pace"]))
        target_dists, target_paces = zip(*sorted(target_points, key=lambda x: x[0]))

        # Get min pace from targets
        min_target_pace = min(target_paces)

        # Generate dotted target pace curve
        x_vals = np.linspace(min_dist, plot_max_dist, 100)
        y_vals = [
            estimate_pace_at_distance(min_target_pace, target_dists[0], d)
            for d in x_vals
        ]
        ax.plot(x_vals, y_vals, "g-.", label="Min Target Pace", alpha=0.7)

        ax.scatter(
            target_dists,
            target_paces,
            color="green",
            marker="x",
            s=100,
            label="Next Targets",
        )

    # Plot raw data (blue dots)
    ax.scatter(df["Distance"], df["Pace"], label="All Runs", alpha=0.6)

    ax.set_title(f"Pace vs. Distance for {Exercise}")
    ax.set_xlabel("Distance (miles)")
    ax.set_ylabel("Pace (seconds/mile, lower=faster)")
    ax.set_xlim(left=0, right=plot_max_dist)
    ax.legend()

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
    df_targets = df_next_running_targets(df_records)

    # Format pace columns for display
    if not df_targets.empty:
        df_targets_display = df_targets.copy()
        df_targets_display["Pace"] = df_targets_display["Pace"].apply(
            seconds_to_pace_string
        )
        df_targets_display["Speed"] = df_targets_display["Speed"].round(2)
    else:
        df_targets_display = df_targets

    figures_html: dict[str, str] = {}

    def slugify(name: str) -> str:
        slug = re.sub(r"[^\w]+", "_", name)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug.lower()

    exercise_slug = {ex: slugify(ex) for ex in df["Exercise"].unique()}

    # Generate plots for each exercise
    for exercise, slug in exercise_slug.items():
        fig = plot_running_df(df, df_records, df_targets, Exercise=exercise)
        buf = BytesIO()
        # Use SVG format instead of PNG for smaller file size and scalability
        fig.savefig(buf, format="svg", bbox_inches="tight")
        buf.seek(0)
        svg_data = buf.read().decode("utf-8")
        # Embed SVG directly (smaller than base64-encoded PNG)
        img_html = (
            f'<div id="fig-{slug}" class="running-figure" '
            f'style="display:none; max-width:100%; height:auto;">'
            f"{svg_data}"
            f"</div>"
        )
        figures_html[exercise] = img_html
        plt.close(fig)

    all_figures_html = "\n".join(figures_html.values())

    # Create dropdown
    exercise_options = sorted(df["Exercise"].dropna().unique())
    dropdown_html = """
    <label for="runningDropdown">Filter by Running Activity:</label>
    <select id="runningDropdown">
    <option value="">All</option>
    """
    dropdown_html += "".join(
        f'<option value="{x}" data-fig="{exercise_slug.get(x, "")}">{x}</option>'
        for x in exercise_options
    )
    dropdown_html += """
    </select>
    <br><br>
    """

    # Convert targets to table
    table_html = df_targets_display.to_html(
        classes="display compact cell-border", table_id="runningTable", index=False
    )

    return dropdown_html + table_html + all_figures_html


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
    js_and_css = """
    <!-- Preconnect to CDNs for faster loading -->
    <link rel="preconnect" href="https://code.jquery.com">
    <link rel="preconnect" href="https://cdn.datatables.net">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">

    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js" defer></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js" defer></script>

    <!-- Select2 for searchable dropdown -->
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js" defer></script>

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
        .select2-container--default .select2-selection--single {
            background-color: var(--bg-alt);
            color: var(--fg);
            border: 1px solid var(--border);
        }
        .select2-container--default .select2-selection--single .select2-selection__rendered {
            color: var(--fg);
        }
        .select2-dropdown {
            background-color: var(--bg-alt);
            color: var(--fg);
            border: 1px solid var(--border);
        }
        .select2-results__option--highlighted {
            background-color: var(--bg);
            color: var(--fg);
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
    html[data-theme="dark"] .select2-container--default .select2-selection--single {
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 1px solid var(--border);
    }
    html[data-theme="dark"] .select2-container--default .select2-selection--single .select2-selection__rendered {
        color: var(--fg);
    }
    html[data-theme="dark"] .select2-dropdown {
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 1px solid var(--border);
    }
    html[data-theme="dark"] .select2-results__option--highlighted {
        background-color: var(--bg);
        color: var(--fg);
    }

    #runningDropdown {
        width: 100%;
        max-width: 400px;
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
            order: [[0, 'asc']]
        });

        // Initialize Select2 for dropdown
        $('#runningDropdown').select2();

        // Handle dropdown change to show/hide figures
        $('#runningDropdown').on('change', function() {
            const selectedExercise = $(this).val();
            const selectedFigSlug = $(this).find(':selected').data('fig');

            // Hide all figures
            $('.exercise-figure').hide();

            // Show selected figure (if any)
            if (selectedFigSlug) {
                $(`#fig-${selectedFigSlug}`).show();
            }

            // Filter table rows
            if (selectedExercise) {
                $('#runningTable').DataTable().column(0).search('^' + selectedExercise + '$', true, false).draw();
            } else {
                $('#runningTable').DataTable().column(0).search('').draw();
            }
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
