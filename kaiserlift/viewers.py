import numpy as np
from difflib import get_close_matches
import matplotlib.pyplot as plt
import re
from io import BytesIO
from .df_processers import (
    calculate_1rm,
    highest_weight_per_rep,
    estimate_weight_from_1rm,
    df_next_pareto,
)


def get_closest_exercise(df, Exercise):
    all_exercises = df["Exercise"].unique()
    matches = get_close_matches(Exercise, all_exercises, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    else:
        raise ValueError(f"No close match found for '{Exercise}'.")


def plot_df(df, df_pareto=None, df_targets=None, Exercise: str = None):
    df = df[df["Reps"] != 0]

    if Exercise is None:
        exercises = df["Exercise"].unique()
        fig, ax = plt.subplots()
        for exercise in exercises:
            exercise_df = df[df["Exercise"] == exercise]
            ax.scatter(
                exercise_df["Reps"] / max(exercise_df["Reps"]),
                exercise_df["Weight"] / max(exercise_df["Weight"]),
                label=exercise,
            )
        ax.set_title("Weight vs. Reps for All Exercises")
        ax.set_xlabel("Reps")
        ax.set_ylabel("Weight")
        return fig

    closest_match = get_closest_exercise(df, Exercise)
    df = df[df["Exercise"] == closest_match]
    if df_pareto is not None:
        df_pareto = df_pareto[df_pareto["Exercise"] == closest_match]
    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == closest_match]

    rep_series = [df["Reps"]]
    if df_pareto is not None and not df_pareto.empty:
        rep_series.append(df_pareto["Reps"])
    if df_targets is not None and not df_targets.empty:
        rep_series.append(df_targets["Reps"])

    min_rep = min(series.min() for series in rep_series)
    max_rep = max(series.max() for series in rep_series)
    plot_max_rep = max_rep + 1

    fig, ax = plt.subplots()

    if df_pareto is not None:
        pareto_points = list(zip(df_pareto["Reps"], df_pareto["Weight"]))
        pareto_reps, pareto_weights = zip(*sorted(pareto_points, key=lambda x: x[0]))
        pareto_reps = list(pareto_reps)
        pareto_weights = list(pareto_weights)

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(pareto_weights, pareto_reps)]
        max_1rm = max(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min_rep, plot_max_rep, 10)
        y_vals = [estimate_weight_from_1rm(max_1rm, r) for r in x_vals]
        ax.plot(x_vals, y_vals, "k--", label="Max Achieved 1RM", alpha=0.7)

        ax.step(
            pareto_reps,
            pareto_weights,
            color="red",
            label="Pareto Front",
        )
        ax.scatter(
            pareto_reps,
            pareto_weights,
            color="red",
            marker="o",
            label="_nolegend_",
        )

    if df_targets is not None:
        target_points = list(zip(df_targets["Reps"], df_targets["Weight"]))
        target_reps, target_weights = zip(*sorted(target_points, key=lambda x: x[0]))

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(target_weights, target_reps)]
        min_1rm = min(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min_rep, plot_max_rep, 10)
        y_vals = [estimate_weight_from_1rm(min_1rm, r) for r in x_vals]
        ax.plot(x_vals, y_vals, "g-.", label="Min Target 1RM", alpha=0.7)

        ax.scatter(
            df_targets["Reps"],
            df_targets["Weight"],
            color="green",
            marker="x",
            label="Targets",
        )

    # Plotting
    ax.scatter(df["Reps"], df["Weight"], label="Data Points")

    ax.set_title(f"Weight vs. Reps for {closest_match}")
    ax.set_xlabel("Reps")
    ax.set_xlim(left=0, right=plot_max_rep)
    ax.set_ylabel("Weight")
    ax.legend()

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

    def slugify(name: str) -> str:
        """Return a normalized slug for the given exercise name."""
        slug = re.sub(r"[^\w]+", "_", name)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug.lower()

    exercise_slug = {ex: slugify(ex) for ex in df["Exercise"].unique()}

    for exercise, slug in exercise_slug.items():
        fig = plot_df(df, df_records, df_targets, Exercise=exercise)
        buf = BytesIO()
        # Use SVG format instead of PNG for smaller file size and scalability
        fig.savefig(buf, format="svg", bbox_inches="tight")
        buf.seek(0)
        svg_data = buf.read().decode("utf-8")
        # Embed SVG directly (smaller than base64-encoded PNG)
        img_html = (
            f'<div id="fig-{slug}" class="exercise-figure" '
            f'style="display:none; max-width:100%; height:auto;">'
            f"{svg_data}"
            f"</div>"
        )
        figures_html[exercise] = img_html
        plt.close(fig)

    all_figures_html = "\n".join(figures_html.values())

    exercise_column = "Exercise"  # Adjust if needed
    exercise_options = sorted(df[exercise_column].dropna().unique())

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

    #exerciseDropdown {
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

    .exercise-figure {
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

    .exercise-figure svg {
        max-width: 100%;
        height: auto;
        display: block;
    }

    @media only screen and (max-width: 600px) {
        body {
            padding: 16px;
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
    <div class="upload-controls">
        <input type="file" id="csvFile">
        <button id="uploadButton">Upload ⬆️</button>
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
    toggle_html = (
        '<button id="themeToggle" '
        'style="position:fixed;top:16px;right:16px;'
        "padding:10px 14px;"
        "background:var(--bg-alt);color:var(--fg);"
        "border:2px solid var(--border);"
        "border-radius:8px;"
        "cursor:pointer;"
        "font-size:24px;"
        "box-shadow:var(--shadow);"
        "transition:all 0.2s ease;"
        'z-index:1000;"'
        "onmouseover=\"this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 6px rgba(0,0,0,0.15)'\" "
        "onmouseout=\"this.style.transform='translateY(0)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)'\">"
        "🌓</button>"
    )
    theme_script = """
    <script>
    document.getElementById('themeToggle').addEventListener('click', () => {
      const root = document.documentElement;
      const current = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', current);
    });
    </script>
    """
    body_html = (
        toggle_html + upload_html + f'<div id="result">{fragment}</div>' + theme_script
    )
    return f"<html><head>{head_html}</head><body>{body_html}</body></html>"
