from html import escape
from .dashboard import render_dashboard
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
                line=dict(color="#4979aa", shape="vh", width=2),
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
                marker=dict(color="#4979aa", size=10, symbol="circle"),
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
                marker=dict(color="#236b45", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{y} lbs<br>"
                + "1RM: %{customdata:.1f}<extra></extra>",
                customdata=target_one_rms,
            )
        )

    fig.update_layout(
        title=None,
        xaxis_title="Reps",
        yaxis_title="Weight (lbs)",
        xaxis=dict(range=[0, plot_max_rep]),
        hovermode="closest",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        height=520,
        margin=dict(t=24, l=50, r=16, b=100),
    )

    return fig


def plot_df_1rm(df_pareto=None, df_targets=None, Exercise: str = None):
    """Plot estimated 1RM vs Reps using 1RM-space Pareto dominance.

    Companion to :func:`plot_df`: same X-axis (reps), but Y shows the Epley
    1RM estimate rather than raw weight.  The Pareto front uses a different
    dominance rule — a record is kept only when no higher-rep set implies an
    equal or greater estimated 1RM — so the two graphs can diverge.

    Parameters
    ----------
    df_pareto : pd.DataFrame, optional
        1RM-Pareto records (from :func:`highest_1rm_per_rep`). Must contain
        a ``1RM`` column in addition to ``Exercise``, ``Weight``, ``Reps``.
    df_targets : pd.DataFrame, optional
        Target sets (same as used by :func:`plot_df`); their 1RM values are
        derived on the fly.
    Exercise : str, optional
        Exercise to plot. Must be specified.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if df_pareto is None or df_pareto.empty:
        raise ValueError("df_pareto must be provided and non-empty")

    if Exercise is None:
        raise ValueError("Exercise must be specified")

    closest_match = get_closest_exercise(df_pareto, Exercise)
    df_pareto = df_pareto[df_pareto["Exercise"] == closest_match].copy()
    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == closest_match].copy()

    # Ensure 1RM column is present
    if "1RM" not in df_pareto.columns:
        df_pareto["1RM"] = df_pareto.apply(
            lambda row: calculate_1rm(row["Weight"], row["Reps"]), axis=1
        )

    rep_series = [df_pareto["Reps"]]
    if df_targets is not None and not df_targets.empty:
        rep_series.append(df_targets["Reps"])

    min_rep = min(series.min() for series in rep_series)
    max_rep = max(series.max() for series in rep_series)
    plot_max_rep = max_rep + 1

    # Compute target 1RMs
    target_one_rms = []
    if df_targets is not None and not df_targets.empty:
        target_one_rms = [
            calculate_1rm(w, r)
            for w, r in zip(df_targets["Weight"], df_targets["Reps"])
        ]

    # Y-axis range
    all_1rms = list(df_pareto["1RM"].dropna())
    if target_one_rms:
        all_1rms.extend(target_one_rms)
    y_lo = min(all_1rms) * 0.85 if all_1rms else 0
    y_hi = max(all_1rms) * 1.15 if all_1rms else 100

    fig = go.Figure()

    # Pareto points in 1RM space
    if not df_pareto.empty:
        pareto_points = list(
            zip(df_pareto["Reps"], df_pareto["1RM"], df_pareto["Weight"])
        )
        pareto_points.sort(key=lambda x: x[0])
        pareto_reps = [p[0] for p in pareto_points]
        pareto_1rms = [p[1] for p in pareto_points]
        pareto_weights = [p[2] for p in pareto_points]

        best_1rm = max(pareto_1rms)
        x_line = [min_rep, plot_max_rep]

        # Best 1RM horizontal reference line
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=[best_1rm, best_1rm],
                mode="lines",
                name="Best 1RM",
                line=dict(color="black", dash="dash", width=2),
                opacity=0.7,
                hovertemplate=f"<b>Best 1RM</b><br>1RM: {best_1rm:.1f} lbs<extra></extra>",
            )
        )

        # 1RM Pareto staircase
        fig.add_trace(
            go.Scatter(
                x=pareto_reps,
                y=pareto_1rms,
                mode="lines",
                name="Pareto Front (1RM)",
                line=dict(color="red", shape="vh", width=2),
                hovertemplate="<b>Pareto Front</b><extra></extra>",
            )
        )

        # 1RM Pareto markers
        fig.add_trace(
            go.Scatter(
                x=pareto_reps,
                y=pareto_1rms,
                mode="markers",
                name="Pareto Points",
                marker=dict(color="red", size=10, symbol="circle"),
                hovertemplate="<b>Pareto Point</b><br>"
                + "Reps: %{x}<br>"
                + "1RM: %{y:.1f} lbs<br>"
                + "Weight: %{customdata} lbs<extra></extra>",
                customdata=pareto_weights,
                showlegend=False,
            )
        )

    # Targets
    if df_targets is not None and not df_targets.empty and target_one_rms:
        target_points = list(
            zip(df_targets["Reps"], df_targets["Weight"], target_one_rms)
        )
        target_points.sort(key=lambda x: x[0])
        target_reps = [p[0] for p in target_points]
        target_weights = [p[1] for p in target_points]
        sorted_target_1rms = [p[2] for p in target_points]

        min_target_1rm = min(target_one_rms)

        # Lowest target 1RM horizontal reference line
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=[min_target_1rm, min_target_1rm],
                mode="lines",
                name="Lowest Target 1RM",
                line=dict(color="green", dash="dot", width=2),
                opacity=0.7,
                hovertemplate=f"<b>Target 1RM</b><br>1RM: {min_target_1rm:.1f} lbs<extra></extra>",
            )
        )

        # Target markers
        fig.add_trace(
            go.Scatter(
                x=target_reps,
                y=sorted_target_1rms,
                mode="markers",
                name="Targets",
                marker=dict(color="green", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Reps: %{x}<br>"
                + "Weight: %{customdata} lbs<br>"
                + "1RM: %{y:.1f} lbs<extra></extra>",
                customdata=target_weights,
            )
        )

    fig.update_layout(
        title=(
            f"Estimated 1RM vs. Reps for {closest_match}<br><sup>"
            "1RM via Epley: 1RM = weight \u00d7 (1 + (reps\u22121)/30); "
            "Pareto dominance: a point is kept only if no set with more reps "
            "implies an equal or greater estimated 1RM.</sup>"
        ),
        xaxis_title="Reps",
        yaxis_title="Estimated 1RM (lbs)",
        xaxis=dict(range=[0, plot_max_rep]),
        yaxis=dict(range=[y_lo, y_hi]),
        hovermode="closest",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        height=520,
        margin=dict(t=100, l=60, r=20, b=140),
    )

    return fig


def plot_df_combined(
    df_weight_pareto=None,
    df_1rm_pareto=None,
    df_targets=None,
    Exercise: str = None,
):
    """Combined two-row subplot: Weight vs Reps (top) + Estimated 1RM vs Reps (bottom).

    The X-axis (reps) is shared between both subplots so that zooming or panning
    on one row automatically updates the other.

    Parameters
    ----------
    df_weight_pareto : pd.DataFrame, optional
        Weight-Pareto records (from highest_weight_per_rep).
    df_1rm_pareto : pd.DataFrame, optional
        1RM-Pareto records (from highest_1rm_per_rep).
    df_targets : pd.DataFrame, optional
        Target sets (same for both subplots).
    Exercise : str, optional
        Exercise to plot.

    Returns
    -------
    plotly.graph_objects.Figure
        Single combined subplot figure.
    """
    from plotly.subplots import make_subplots

    fig_weight = plot_df(df_weight_pareto, df_targets, Exercise=Exercise)
    fig_1rm = plot_df_1rm(df_1rm_pareto, df_targets, Exercise=Exercise)

    combined = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=["Weight vs. Reps", "Estimated 1RM vs. Reps"],
    )

    # Add weight traces to row 1
    weight_trace_names = {t.name for t in fig_weight.data if t.name}
    for trace in fig_weight.data:
        combined.add_trace(trace, row=1, col=1)

    # Add 1RM traces to row 2; suppress legend entries already shown in row 1
    for trace in fig_1rm.data:
        if trace.name in weight_trace_names:
            trace.showlegend = False
        combined.add_trace(trace, row=2, col=1)

    # Shared x-axis: label on bottom subplot only
    wl = fig_weight.layout
    combined.update_xaxes(range=list(wl.xaxis.range))
    combined.update_xaxes(title_text="Reps", row=2, col=1)

    # Row 1 y-axis: weight
    combined.update_yaxes(title_text="Weight (lbs)", row=1, col=1)

    # Row 2 y-axis: 1RM with explicit range from the individual figure
    ol = fig_1rm.layout
    combined.update_yaxes(
        range=list(ol.yaxis.range),
        title_text="Estimated 1RM (lbs)",
        row=2,
        col=1,
    )

    closest = get_closest_exercise(df_weight_pareto, Exercise)
    combined.update_layout(
        title=(
            f"Lifting Performance: {closest}<br><sup>"
            "Red\u202f=\u202fPareto front \u00b7 Black\u202f=\u202fBest Epley curve \u00b7 "
            "Green\u202f=\u202fNext targets \u00b7 X-axes linked for synchronized zoom.</sup>"
        ),
        hovermode="closest",
        template="plotly_white",
        height=880,
        margin=dict(t=80, l=60, r=20, b=100),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.06,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    return combined


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

    The fragment contains the exercise selector, charts, recommendation panels,
    and target table. Inert JSON script tags hold chart specifications; the
    surrounding page supplies assets and calls ``initializeDashboard`` after
    inserting a fragment.
    """

    df_records = highest_weight_per_rep(df)
    df_targets = df_next_pareto(df_records)

    exercises = sorted(df_records["Exercise"].dropna().unique())
    panels = []
    options = []
    for index, exercise in enumerate(exercises):
        slug = f"{index}-{slugify(exercise)}"
        name = escape(str(exercise), quote=True)
        options.append(f'<option value="{name}">{name}</option>')
        fig = plot_df(df_records, df_targets, Exercise=exercise)
        targets = df_targets[df_targets["Exercise"] == exercise].sort_values("1RM")
        target_text = "No targets available"
        if not targets.empty:
            target = targets.iloc[0]
            target_text = f"{target['Weight']:g} lbs × {target['Reps']:g} reps"
            fig.add_trace(
                go.Scatter(
                    x=[target["Reps"]],
                    y=[target["Weight"]],
                    mode="markers",
                    name="Recommended target",
                    marker=dict(color="#236b45", size=17, symbol="star"),
                    hovertemplate="Recommended target<br>%{y} lbs × %{x} reps<extra></extra>",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="markers",
                name="Selected target",
                showlegend=False,
                marker=dict(
                    color="#213c32", size=20, symbol="diamond-open", line=dict(width=3)
                ),
                hoverinfo="skip",
            )
        )
        chart = plotly_figure_to_html_div(fig, slug, display="block")
        hidden = " hidden" if index else ""
        panels.append(f"""
        <section data-exercise-panel="{name}"{hidden}>
            <div class="dashboard-grid">
                <div class="chart-card">
                    <div class="chart-heading"><h3>{name}</h3>
                    <div class="chart-controls"><button data-chart-action="reset" aria-label="Reset chart zoom">Reset view</button>
                    <button data-chart-action="export" aria-label="Export chart as PNG">Save plot ↗</button></div></div>
                    {chart}
                    <details class="chart-help">
                        <summary>How to read this graph</summary>
                        <p>Circles show your best recorded sets; crosses show potential
                        new records. The star marks the target with the lowest estimated
                        one-rep maximum. Tap a target to see its weight and reps.</p>
                        <p>Dotted curves compare sets using the Epley estimate.
                        Targets add weight or reps to your recorded performances.
                        Estimated one-rep maximums help compare different rep counts.</p>
                    </details>
                </div>
                <aside class="target-card" aria-label="Workout recommendation">
                    <span class="eyebrow" data-target-label>Next target</span>
                    <output class="target-value" aria-live="polite">{target_text}</output>
                    <p data-target-explanation>This target has the lowest estimated one-rep maximum
                    among this exercise's proposed records.</p>
                    <p>Select a cross on the graph or a row below to explore another target.</p>
                </aside>
            </div>
        </section>
        """)
    table_html = df_targets.round({"1RM": 1}).to_html(
        classes="display compact cell-border",
        table_id="exerciseTable",
        index=False,
        float_format=lambda value: f"{value:.15g}",
    )
    return f"""
    <section id="performance" data-lab-view="neo-retro" class="content-card">
        <div class="dashboard-toolbar">
            <div><p class="eyebrow">01 / Performance map</p><h2>Weight × Reps</h2></div>
            <div class="control-stack">
                <label for="exerciseDropdown">Exercise</label>
                <select id="exerciseDropdown">{"".join(options)}</select>
            </div>
        </div>
        <div class="figures-grid">{"".join(panels)}</div>
    </section>
    <section id="targets" class="content-card target-table">
        <div class="section-heading"><h2>02 / Target register</h2><span>Select a row to inspect a target ↗</span></div>
        <div class="table-wrapper">{table_html}</div>
    </section>
    """


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

    return render_dashboard(fragment, mode="lifting")
