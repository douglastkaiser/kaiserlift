import numpy as np
from difflib import get_close_matches
import matplotlib.pyplot as plt
import base64
import re
from io import BytesIO
import pandas as pd
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

    fig, ax = plt.subplots()

    if df_pareto is not None:
        pareto_points = list(zip(df_pareto["Reps"], df_pareto["Weight"]))
        pareto_reps, pareto_weights = zip(*sorted(pareto_points, key=lambda x: x[0]))

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(pareto_weights, pareto_reps)]
        max_1rm = max(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min(df["Reps"]), max(df["Reps"]), 10)
        y_vals = [estimate_weight_from_1rm(max_1rm, r) for r in x_vals]
        ax.plot(x_vals, y_vals, "k--", label="Max Achieved 1RM", alpha=0.7)

        ax.step(
            pareto_reps, pareto_weights, color="red", marker="o", label="Pareto Front"
        )

    if df_targets is not None:
        target_points = list(zip(df_targets["Reps"], df_targets["Weight"]))
        target_reps, target_weights = zip(*sorted(target_points, key=lambda x: x[0]))

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(target_weights, target_reps)]
        min_1rm = min(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min(df["Reps"]), max(df["Reps"]), 10)
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
    ax.set_xlim(left=0)
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


def render_viewer_fragment(df: pd.DataFrame) -> str:
    """Return the HTML fragment for the exercise viewer.

    The fragment contains the dropdown, data table and generated figures but no
    surrounding page scaffolding.
    """

    df_records = highest_weight_per_rep(df)
    df_targets = df_next_pareto(df_records)

    figures_html: dict[str, str] = {}
    errors = ""

    def slugify(name: str) -> str:
        """Return a normalized slug for the given exercise name."""
        slug = re.sub(r"[^\w]+", "_", name)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug.lower()

    exercise_slug = {ex: slugify(ex) for ex in df["Exercise"].unique()}

    for exercise, slug in exercise_slug.items():
        try:
            fig = plot_df(df, df_records, df_targets, Exercise=exercise)
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            base64_img = base64.b64encode(buf.read()).decode("utf-8")
            img_html = (
                f'<img src="data:image/png;base64,{base64_img}" '
                f'id="fig-{slug}" class="exercise-figure" '
                'style="display:none; max-width:100%; height:auto;">'
            )
            figures_html[exercise] = img_html
            plt.close(fig)
        except Exception as e:  # pragma: no cover - visualization errors
            errors += f"{e}"

    all_figures_html = "\n".join(figures_html.values())

    exercise_options = sorted(df["Exercise"].dropna().unique())

    dropdown_html = """\
    <label for="exerciseDropdown">Filter by Exercise:</label>
    <select id="exerciseDropdown">
    <option value="">All</option>
    """
    dropdown_html += "".join(
        f'<option value="{x}" data-fig="{exercise_slug.get(x, "")}">{x}</option>'
        for x in exercise_options
    )
    dropdown_html += """\
    </select>
    <br><br>
    """

    table_html = df_targets.to_html(
        classes="display compact cell-border", table_id="exerciseTable", index=False
    )

    return dropdown_html + table_html + all_figures_html


def gen_html_viewer(df: pd.DataFrame) -> str:
    """Return a full HTML page for viewing exercise data.

    The page exposes a file input and upload button that posts to ``/upload``
    using ``fetch``. On success the viewer content is replaced with the server's
    response and DataTables/Select2 are reinitialized.
    """

    fragment = render_viewer_fragment(df)

    css_and_js_links = """\
    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>

    <!-- Select2 for searchable dropdown -->
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

    <!-- Custom Styling for Mobile -->
    <style>
    body {
        font-family: Arial, sans-serif;
        font-size: 34px;
        padding: 28px;
    }

    table.dataTable {
        font-size: 32px;
        width: 100% !important;
        word-wrap: break-word;
    }

    label, select {
        font-size: 34px;
    }

    #exerciseDropdown {
        width: 100%;
        max-width: 400px;
    }

    @media only screen and (max-width: 600px) {
        table, thead, tbody, th, td, tr {
        display: block;
        }
        th {
        text-align: left;
        }
    }
    </style>
    """

    script = """\
    <script>
    function initViewer() {
        var table = $('#exerciseTable').DataTable({
            responsive: true
        });

        $('#exerciseDropdown').select2({
            placeholder: "Filter by Exercise",
            allowClear: true
        });

        $('#exerciseDropdown').on('change', function() {
            var val = $.fn.dataTable.util.escapeRegex($(this).val());
            table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();

            $('.exercise-figure').hide();

            var figId = $(this).find('option:selected').data('fig');
            if (figId) {
                $('#fig-' + figId).show();
            }
        });
    }

    async function uploadCSV() {
        const fileInput = document.getElementById('csvFile');
        if (!fileInput.files.length) {
            return;
        }
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const html = await response.text();
            document.getElementById('viewerContainer').innerHTML = html;
            initViewer();
        }
    }

    document.getElementById('uploadBtn').addEventListener('click', uploadCSV);
    $(document).ready(function() {
        initViewer();
    });
    </script>
    """

    full_html = (
        css_and_js_links
        + """\
    <div>
        <input type=\"file\" id=\"csvFile\">
        <button id=\"uploadBtn\">Upload</button>
    </div>
    <div id=\"viewerContainer\">
    """
        + fragment
        + """\
    </div>
    """
        + script
    )

    return full_html
