import numpy as np
from difflib import get_close_matches
import plotly.graph_objects as go
from .df_processers import (
    calculate_1rm,
    highest_weight_per_rep,
    estimate_weight_from_1rm,
    df_next_pareto,
)
from .plot_utils import (
    slugify,
    plotly_figure_to_html_div,
    get_plotly_cdn_html,
    get_plotly_preconnect_html,
)


def get_closest_exercise(df, Exercise):
    all_exercises = df["Exercise"].unique()
    matches = get_close_matches(Exercise, all_exercises, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    else:
        raise ValueError(f"No close match found for '{Exercise}'.")


def plot_df(df_pareto=None, df_targets=None, Exercise: str = None):
    if df_pareto is None or df_pareto.empty:
        raise ValueError("df_pareto must be provided and non-empty")

    if Exercise is None:
        raise ValueError("Exercise must be specified")

    closest_match = get_closest_exercise(df_pareto, Exercise)
    df_pareto = df_pareto[df_pareto["Exercise"] == closest_match]
    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == closest_match]

    rep_series = [df_pareto["Reps"]]
    if df_targets is not None and not df_targets.empty:
        rep_series.append(df_targets["Reps"])

    min_rep = min(series.min() for series in rep_series)
    max_rep = max(series.max() for series in rep_series)
    plot_max_rep = max_rep + 1

    fig = go.Figure()

    if df_pareto is not None and not df_pareto.empty:
        pareto_points = list(zip(df_pareto["Reps"], df_pareto["Weight"]))
        pareto_reps, pareto_weights = zip(*sorted(pareto_points, key=lambda x: x[0]))
        pareto_reps = list(pareto_reps)
        pareto_weights = list(pareto_weights)

        # Compute best 1RM from Pareto front and anchor the line to that point
        one_rms = [calculate_1rm(w, r) for w, r in zip(pareto_weights, pareto_reps)]
        best_idx = int(np.argmax(one_rms))
        max_1rm = one_rms[best_idx]
        anchor_rep = pareto_reps[best_idx]
        anchor_weight = pareto_weights[best_idx]

        # Generate dotted Epley decay line (ensure it passes through the anchor)
        x_vals = np.linspace(min_rep, plot_max_rep, 100).tolist()
        x_vals.append(anchor_rep)
        x_vals = sorted(set(x_vals))

        y_vals = [estimate_weight_from_1rm(max_1rm, r) for r in x_vals]
        anchor_idx = x_vals.index(anchor_rep)
        y_vals[anchor_idx] = anchor_weight
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name="Max Achieved 1RM",
                line=dict(color="black", dash="dash", width=2),
                opacity=0.7,
                hovertemplate="<b>Max 1RM Curve</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{y:.1f} lbs<br>"
                + f"1RM: {max_1rm:.1f}<extra></extra>",
            )
        )

        # Pareto step line
        fig.add_trace(
            go.Scatter(
                x=pareto_reps,
                y=pareto_weights,
                mode="lines",
                name="Pareto Front",
                line=dict(color="red", shape="vh", width=2),
                hovertemplate="<b>Pareto Front</b><extra></extra>",
            )
        )

        # Pareto markers
        fig.add_trace(
            go.Scatter(
                x=pareto_reps,
                y=pareto_weights,
                mode="markers",
                name="Pareto Points",
                marker=dict(color="red", size=10, symbol="circle"),
                hovertemplate="<b>Pareto Point</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{y} lbs<br>"
                + "1RM: %{customdata:.1f}<extra></extra>",
                customdata=one_rms,
                showlegend=False,
            )
        )

    if df_targets is not None and not df_targets.empty:
        target_points = list(zip(df_targets["Reps"], df_targets["Weight"]))
        target_reps, target_weights = zip(*sorted(target_points, key=lambda x: x[0]))

        target_one_rms = [
            calculate_1rm(w, r) for w, r in zip(target_weights, target_reps)
        ]

        # Lowest target 1RM equivalence line (anchored to the weakest target)
        weakest_idx = int(np.argmin(target_one_rms))
        min_target_1rm = target_one_rms[weakest_idx]
        target_anchor_rep = target_reps[weakest_idx]
        target_anchor_weight = target_weights[weakest_idx]

        x_vals = np.linspace(min_rep, plot_max_rep, 100).tolist()
        x_vals.append(target_anchor_rep)
        x_vals = sorted(set(x_vals))

        target_curve = [estimate_weight_from_1rm(min_target_1rm, r) for r in x_vals]
        anchor_idx = x_vals.index(target_anchor_rep)
        target_curve[anchor_idx] = target_anchor_weight
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=target_curve,
                mode="lines",
                name="Lowest Target 1RM",
                line=dict(color="green", dash="dot", width=2),
                opacity=0.7,
                hovertemplate="<b>Target 1RM Curve</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{y:.1f} lbs<br>"
                + f"1RM: {min_target_1rm:.1f}<extra></extra>",
            )
        )

        # Target markers
        fig.add_trace(
            go.Scatter(
                x=target_reps,
                y=target_weights,
                mode="markers",
                name="Targets",
                marker=dict(color="green", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{y} lbs<br>"
                + "1RM: %{customdata:.1f}<extra></extra>",
                customdata=target_one_rms,
            )
        )

    fig.update_layout(
        title=f"Weight vs. Reps for {closest_match}",
        xaxis_title="Reps",
        yaxis_title="Weight (lbs)",
        xaxis=dict(range=[0, plot_max_rep]),
        hovermode="closest",
        template="plotly_white",
    )

    return fig


def print_oldest_exercise(
    df, n_cat=2, n_exercises_per_cat=2, n_target_sets_per_exercises=2
) -> None:
    df_records = highest_weight_per_rep(df)
    df_targets = df_next_pareto(df_records)

    # Find the most recent date for each category
    category_most_recent = df.groupby("Category")["Date"].max()

    # Sort categories by their most recent date (oldest first)
    sorted_categories = category_most_recent.sort_values().index
    output_lines = []

    for category in sorted_categories[
        :n_cat
    ]:  # Take the category with oldest most recent date
        print(f"{category=}")
        output_lines.append(f"Category: {category}\n")

        # Filter to this category
        category_df = df[df["Category"] == category]

        # Find the oldest exercises in this category
        exercise_oldest_dates = category_df.groupby("Exercise")["Date"].max()
        oldest_exercises = exercise_oldest_dates.nsmallest(n_exercises_per_cat)

        for exercise, oldest_date in oldest_exercises.items():
            print(f"  {exercise=}, date={oldest_date}")
            output_lines.append(f"  Exercise: {exercise}, Last Done: {oldest_date}\n")

            # Find the lowest 3 sets to target
            sorted_exercise_targets = df_targets[
                df_targets["Exercise"] == exercise
            ].nsmallest(n=n_target_sets_per_exercises, columns="1RM")
            for index, row in sorted_exercise_targets.iterrows():
                print(
                    f"    {row['Weight']} for {row['Reps']} reps ({row['1RM']:.2f} 1rm)"
                )
                output_lines.append(
                    f"    {row['Weight']} lbs for {row['Reps']} reps ({row['1RM']:.2f} 1RM)\n"
                )

        print(" ")
        output_lines.append("\n")  # Add a blank line between categories

    return output_lines


def render_table_fragment(df) -> str:
    """Render the viewer fragment without external assets.

    The returned HTML contains only the dropdown, table, and figures while
    omitting any ``<script>`` or ``<link>`` tags so that assets can be injected
    separately.
    """

    df_records = highest_weight_per_rep(df)
    df_targets = df_next_pareto(df_records)

    figures_html: dict[str, str] = {}

    exercise_slug = {ex: slugify(ex) for ex in df_records["Exercise"].unique()}

    for exercise, slug in exercise_slug.items():
        fig = plot_df(df_records, df_targets, Exercise=exercise)
        # Convert Plotly figure to HTML div with wrapper
        img_html = plotly_figure_to_html_div(fig, slug, display="none")
        figures_html[exercise] = img_html

    all_figures_html = "\n".join(figures_html.values())

    exercise_column = "Exercise"  # Adjust if needed
    exercise_options = sorted(df_records[exercise_column].dropna().unique())

    dropdown_html = """
    <label for="exerciseDropdown">Filter by Exercise:</label>
    <select id="exerciseDropdown">
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

    table_html = df_targets.to_html(
        classes="display compact cell-border", table_id="exerciseTable", index=False
    )

    return dropdown_html + table_html + all_figures_html


def gen_html_viewer(df, *, embed_assets: bool = True) -> str:
    """Generate the full viewer HTML.

    Parameters
    ----------
    df:
        Source DataFrame.
    embed_assets:
        If ``True`` (default), include ``<script>`` and ``<link>`` tags for a
        standalone page. When ``False`` only the HTML fragment from
        :func:`render_table_fragment` is returned.
    """

    fragment = render_table_fragment(df)
    if not embed_assets:
        return fragment

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
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>

    <!-- Select2 for searchable dropdown -->
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

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

    /* Select2 styling */
    .select2-container--default .select2-selection--single {
        height: 40px;
        border: 1px solid var(--border);
        border-radius: 4px;
    }

    .select2-container--default .select2-selection--single .select2-selection__rendered {
        line-height: 40px;
        padding-left: 12px;
        color: var(--fg);
    }

    .select2-container--default .select2-selection--single .select2-selection__arrow {
        height: 38px;
    }

    .select2-dropdown {
        border: 1px solid var(--border);
        border-radius: 4px;
    }

    .select2-results__option--highlighted {
        background-color: var(--primary-green) !important;
    }

    #exerciseDropdown {
        width: 100%;
        max-width: 400px;
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

    #clearButton {
        padding: 10px 20px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background-color: var(--bg-alt);
        color: var(--fg);
        cursor: pointer;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
        min-height: 40px;
    }

    #clearButton:hover {
        background-color: var(--bg);
        border-color: var(--fg-light);
    }

    /* Chart container styling */
    .exercise-figure {
        border-radius: 4px;
        box-shadow: var(--shadow);
        margin: 25px 0;
        opacity: 0;
        animation: fadeIn 0.3s ease-in forwards;
        width: 100%;
        overflow: hidden;
        background-color: var(--bg-alt);
    }

    .exercise-figure .js-plotly-plot,
    .exercise-figure .plotly {
        width: 100% !important;
    }

    .exercise-figure .main-svg {
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

    .exercise-figure svg {
        max-width: 100%;
        height: auto;
        display: block;
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

        #uploadButton,
        #clearButton {
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

        #exerciseDropdown {
            max-width: 100%;
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
        <p class="subtitle">Lifting Data Analysis</p>
    </div>
    <div class="upload-controls">
        <input type="file" id="csvFile">
        <button id="uploadButton">Upload</button>
        <button id="clearButton">Clear</button>
        <progress id="uploadProgress" value="0" max="100" style="display:none;"></progress>
    </div>
    """

    scripts = """
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js" defer></script>
    <script type="module" src="main.js"></script>
    """
    meta = """
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="description" content="KaiserLift workout analysis - Data-driven progressive overload with Pareto optimization">
    """
    head_html = meta + js_and_css + scripts
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
    interactive_script = """
    <script>
    $(document).ready(function() {
        const tableEl = $('#exerciseTable');
        const dropdownEl = $('#exerciseDropdown');

        const table = ($.fn.DataTable && $.fn.DataTable.isDataTable(tableEl))
            ? tableEl.DataTable()
            : tableEl.DataTable({ responsive: true });

        dropdownEl
            .select2({ placeholder: 'Filter by Exercise', allowClear: true })
            .on('change', function() {
                const val = $.fn.dataTable.util.escapeRegex($(this).val());
                table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();
                $('.exercise-figure').hide();
                const figId = $(this).find('option:selected').data('fig');
                if (figId) {
                    $('#fig-' + figId + '-wrapper').show();
                }
            });

        const initialFig = dropdownEl.find('option:selected').data('fig');
        if (initialFig) {
            $('#fig-' + initialFig + '-wrapper').show();
        }
    });
    </script>
    """

    body_html = (
        upload_html
        + f'<div id="result">{fragment}</div>'
        + interactive_script
        + version_footer
    )
    return f"<html><head>{head_html}</head><body>{body_html}</body></html>"
