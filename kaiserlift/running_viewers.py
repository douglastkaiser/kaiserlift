"""Running data visualization module for KaiserLift.

This module provides plotting and HTML generation functionality for
running/cardio data visualization.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from .running_processers import (
    SECONDS_PER_HOUR,
    highest_pace_per_distance,
    highest_pace_per_distance_pace_pareto,
    df_next_running_targets,
    seconds_to_pace_string,
    add_speed_metric_column,
    estimate_pace_at_distance,
    riegel_pace_exponent,
)
from .plot_utils import (
    slugify,
    plotly_figure_to_html_div,
    get_plotly_cdn_html,
    get_plotly_preconnect_html,
)


def _format_duration_minutes(minutes: float) -> str:
    """Format a duration in minutes as H:MM:SS or M:SS string."""
    if pd.isna(minutes) or minutes <= 0:
        return "N/A"
    total_seconds = int(round(minutes * 60))
    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def plot_running_df(df_pareto=None, df_targets=None, Exercise: str = None):
    """Plot running performance: Distance vs Total Time.

    Similar to plot_df for lifting but with running metrics:
    - X-axis: Distance (miles)
    - Y-axis: Total Time (minutes, lower is better)
    - Red line: Pareto front of best times
    - Green X: Target times to achieve

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

    # Filter to specified exercise and compute Duration (total time in minutes)
    if df_pareto is not None:
        df_pareto = df_pareto[df_pareto["Exercise"] == Exercise].copy()
        if "Duration" not in df_pareto.columns:
            if "Pace" in df_pareto.columns:
                df_pareto["Duration"] = df_pareto["Pace"] * df_pareto["Distance"] / 60.0
            elif "Speed" in df_pareto.columns:
                df_pareto["Duration"] = (
                    df_pareto["Distance"] / df_pareto["Speed"] * 60.0
                )
        if "Speed" not in df_pareto.columns and "Pace" in df_pareto.columns:
            df_pareto["Speed"] = df_pareto["Pace"].apply(
                lambda p: SECONDS_PER_HOUR / p if pd.notna(p) and p > 0 else np.nan
            )

    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == Exercise].copy()
        if "Duration" not in df_targets.columns:
            if "Pace" in df_targets.columns:
                df_targets["Duration"] = (
                    df_targets["Pace"] * df_targets["Distance"] / 60.0
                )
            elif "Speed" in df_targets.columns:
                df_targets["Duration"] = (
                    df_targets["Distance"] / df_targets["Speed"] * 60.0
                )

    # Common race distances for vertical marker lines
    race_distances = [
        (3.10686, "5K"),
        (13.1094, "Half Marathon"),
        (26.2188, "Marathon"),
    ]

    # Calculate axis limits with padding so data points aren't at the edges.
    # Curves/lines may extend to the edges but the data points get breathing room.
    distance_series = [df_pareto["Distance"]]
    if df_targets is not None and not df_targets.empty:
        distance_series.append(df_targets["Distance"])

    min_dist = min(s.min() for s in distance_series)
    max_dist = max(s.max() for s in distance_series)
    plot_min_dist = min_dist * 0.7
    plot_max_dist = max_dist * 1.3

    # Extend the plot range to include any race distance lines that fall
    # near the data so they aren't clipped off the edge of the chart.
    for race_dist, _ in race_distances:
        if race_dist <= max_dist:
            plot_min_dist = min(plot_min_dist, race_dist * 0.85)
        if race_dist >= min_dist:
            plot_max_dist = max(plot_max_dist, race_dist * 1.15)

    fig = go.Figure()

    # Initialize anchor parameters for the Riegel time curve
    best_distance = np.nan
    anchor_duration = np.nan

    # Plot Pareto front (red line)
    if df_pareto is not None and not df_pareto.empty:
        pareto_points = list(zip(df_pareto["Distance"], df_pareto["Duration"]))
        pareto_dists, pareto_durations = zip(*sorted(pareto_points, key=lambda x: x[0]))

        # Find the Pareto point with the best pace (max speed) to anchor the
        # Riegel curve — same anchor logic as before, just displayed in time space.
        if "Speed" in df_pareto.columns:
            max_speed_idx = int(df_pareto["Speed"].idxmax())
            best_distance = float(df_pareto.loc[max_speed_idx, "Distance"])
            anchor_duration = float(df_pareto.loc[max_speed_idx, "Duration"])

        # Generate Riegel time curve: T(D) = T_anchor * (D / D_anchor)^(1+exponent(D))
        # The exponent grows with distance to capture ultra-marathon fatigue.
        if not np.isnan(anchor_duration) and not np.isnan(best_distance):
            x_vals = np.linspace(plot_min_dist, plot_max_dist, 100).tolist()
            x_vals.append(float(best_distance))
            x_vals = sorted(set(x_vals))

            y_vals = [
                anchor_duration * (d / best_distance) ** (1 + riegel_pace_exponent(d))
                for d in x_vals
            ]

            # Ensure the curve intersects the anchor Pareto point exactly
            anchor_idx = x_vals.index(best_distance)
            y_vals[anchor_idx] = anchor_duration

            best_curve_times = [_format_duration_minutes(t) for t in y_vals]
            best_curve_paces = [
                seconds_to_pace_string(t * 60.0 / d)
                if t and not np.isnan(t) and t > 0 and d > 0
                else "N/A"
                for t, d in zip(y_vals, x_vals)
            ]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Best Time Curve",
                    line=dict(color="black", dash="dash", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Best Time Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Time: %{customdata[0]}<br>"
                    + "Pace: %{customdata[1]}<extra></extra>",
                    customdata=list(zip(best_curve_times, best_curve_paces)),
                )
            )

        # Pareto step line (vh: vertical-then-horizontal; with the y-axis
        # inverted, this produces the same upper-right staircase shape as the
        # lifting charts where upper-right = better performance)
        pareto_times_hover = [_format_duration_minutes(t) for t in pareto_durations]
        pareto_paces = [
            seconds_to_pace_string(t * 60.0 / d) if t > 0 and d > 0 else "N/A"
            for t, d in zip(pareto_durations, pareto_dists)
        ]
        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_durations),
                mode="lines",
                name="Pareto Front (Best Times)",
                line=dict(color="red", shape="vh", width=2),
                hovertemplate="<b>Pareto Front</b><extra></extra>",
            )
        )

        # Pareto markers
        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_durations),
                mode="markers",
                name="Pareto Points",
                marker=dict(color="red", size=10, symbol="circle"),
                hovertemplate="<b>Pareto Point</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Time: %{customdata[0]}<br>"
                + "Pace: %{customdata[1]}<extra></extra>",
                customdata=list(zip(pareto_times_hover, pareto_paces)),
                showlegend=False,
            )
        )

    # Plot targets (green X)
    if df_targets is not None and not df_targets.empty:
        target_points = list(zip(df_targets["Distance"], df_targets["Duration"]))
        target_dists, target_durations = zip(*sorted(target_points, key=lambda x: x[0]))

        # Pick the easiest target curve: the one whose Riegel time curve has the
        # highest mean time (highest = slowest = closest to current Pareto from
        # below = least improvement required).
        def curve_score_time(
            anchor_distance: float, anchor_dur: float
        ) -> tuple[list, list, float]:
            sample_points = np.linspace(plot_min_dist, plot_max_dist, 100).tolist()
            sample_points.extend([float(d) for d in target_dists])
            sample_points.append(float(anchor_distance))
            sample_points = sorted(set(sample_points))

            y_curve: list[float] = [
                anchor_dur * (d / anchor_distance) ** (1 + riegel_pace_exponent(d))
                for d in sample_points
            ]
            mean_time = float(np.mean(y_curve)) if y_curve else -np.inf
            return sample_points, y_curve, mean_time

        best_curve: tuple[list, list, float] = ([], [], -np.inf)
        anchor_idx = 0
        for i, (t_dist, t_dur) in enumerate(zip(target_dists, target_durations)):
            x_curve, y_curve, score = curve_score_time(t_dist, t_dur)
            if score > best_curve[2]:
                best_curve = (x_curve, y_curve, score)
                anchor_idx = i

        x_vals, y_vals, _ = best_curve
        if x_vals:
            # Ensure target time curve intersects the selected target anchor
            anchor_distance = target_dists[anchor_idx]
            anchor_dur_val = target_durations[anchor_idx]
            if anchor_distance in x_vals:
                y_vals[x_vals.index(anchor_distance)] = anchor_dur_val

            target_curve_times = [_format_duration_minutes(t) for t in y_vals]
            target_curve_paces = [
                seconds_to_pace_string(t * 60.0 / d)
                if t and not np.isnan(t) and t > 0 and d > 0
                else "N/A"
                for t, d in zip(y_vals, x_vals)
            ]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Target Time Curve",
                    line=dict(color="green", dash="dashdot", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Target Time Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Time: %{customdata[0]}<br>"
                    + "Pace: %{customdata[1]}<extra></extra>",
                    customdata=list(zip(target_curve_times, target_curve_paces)),
                )
            )

        # Target markers
        target_times_hover = [_format_duration_minutes(t) for t in target_durations]
        target_paces = [
            seconds_to_pace_string(t * 60.0 / d) if t > 0 and d > 0 else "N/A"
            for t, d in zip(target_durations, target_dists)
        ]
        fig.add_trace(
            go.Scatter(
                x=list(target_dists),
                y=list(target_durations),
                mode="markers",
                name="Next Targets",
                marker=dict(color="green", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Time: %{customdata[0]}<br>"
                + "Pace: %{customdata[1]}<extra></extra>",
                customdata=list(zip(target_times_hover, target_paces)),
            )
        )

    # Collect all duration values for y-axis range
    all_durations = []
    if df_pareto is not None and not df_pareto.empty:
        all_durations.extend(df_pareto["Duration"].dropna().tolist())
    if df_targets is not None and not df_targets.empty:
        all_durations.extend(df_targets["Duration"].dropna().tolist())
    y_lo = min(all_durations) * 0.8 if all_durations else 0
    y_hi = max(all_durations) * 1.2 if all_durations else 100

    # Add vertical dotted lines for common race distances with always-visible
    # labels near the top.  Use add_vline for the line (handles log axes) and
    # a separate annotation with an explicit log10 x-coordinate (Plotly
    # annotations on log axes expect values in log10 space).
    for race_dist, race_label in race_distances:
        if plot_min_dist <= race_dist <= plot_max_dist:
            fig.add_vline(
                x=race_dist,
                line_dash="dot",
                line_color="gray",
                line_width=1,
                opacity=0.6,
            )
            fig.add_annotation(
                x=np.log10(race_dist),
                y=1,
                yref="paper",
                text=race_label,
                showarrow=False,
                font=dict(size=10, color="rgba(150,150,150,0.8)"),
                yanchor="bottom",
                yshift=2,
            )

    fig.update_layout(
        title=(
            f"Total Time vs. Distance for {Exercise}<br><sup>Targets use 10% of the "
            "distance & time deltas between neighboring Pareto points; "
            "Riegel curve: time2 = time1 \u00d7 (d2/d1)^e, "
            "e\u202f=\u202f0.06\u2013-0.14 (grows with distance).</sup>"
        ),
        xaxis_title="Distance (miles)",
        yaxis_title="Total Time (min, upper=faster)",
        xaxis_type="log",
        yaxis_type="log",
        xaxis=dict(range=[np.log10(plot_min_dist), np.log10(plot_max_dist)]),
        yaxis=dict(range=[np.log10(y_hi), np.log10(y_lo)]),
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
        height=540,
        margin=dict(t=120, l=60, r=20, b=150),
    )

    return fig


def _pace_axis_ticks(y_lo: float, y_hi: float) -> tuple[list, list]:
    """Generate tick values and M:SS labels for a pace axis (sec/mile)."""
    pace_range = y_hi - y_lo
    if pace_range <= 120:
        interval = 15
    elif pace_range <= 300:
        interval = 30
    elif pace_range <= 600:
        interval = 60
    else:
        interval = 120
    start = int(y_lo // interval) * interval
    stop = int(y_hi // interval + 1) * interval
    tick_vals = [
        t for t in range(start, stop + 1, interval) if y_lo * 0.95 <= t <= y_hi * 1.05
    ]
    tick_texts = [seconds_to_pace_string(t) for t in tick_vals]
    return tick_vals, tick_texts


def plot_running_pace_df(df_pareto=None, df_targets=None, Exercise: str = None):
    """Plot running performance: Distance vs Pace (min/mi).

    Same colour scheme as plot_running_df but with pace on the Y-axis
    (inverted so faster pace is visually higher) and a pace-based Pareto front
    whose dominance is computed in pace-distance space rather than
    time-distance space.

    Parameters
    ----------
    df_pareto : pd.DataFrame, optional
        Pace-Pareto records (from highest_pace_per_distance_pace_pareto)
    df_targets : pd.DataFrame, optional
        Target running goals (same as used by plot_running_df)
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

    # Filter to exercise and add Speed if missing
    df_pareto = df_pareto[df_pareto["Exercise"] == Exercise].copy()
    if "Speed" not in df_pareto.columns and "Pace" in df_pareto.columns:
        df_pareto["Speed"] = df_pareto["Pace"].apply(
            lambda p: SECONDS_PER_HOUR / p if pd.notna(p) and p > 0 else np.nan
        )

    if df_targets is not None:
        df_targets = df_targets[df_targets["Exercise"] == Exercise].copy()

    # Common race distances for vertical marker lines
    race_distances = [
        (3.10686, "5K"),
        (13.1094, "Half Marathon"),
        (26.2188, "Marathon"),
    ]

    # Calculate axis limits
    distance_series = [df_pareto["Distance"]]
    if df_targets is not None and not df_targets.empty:
        distance_series.append(df_targets["Distance"])

    min_dist = min(s.min() for s in distance_series)
    max_dist = max(s.max() for s in distance_series)
    plot_min_dist = min_dist * 0.7
    plot_max_dist = max_dist * 1.3

    for race_dist, _ in race_distances:
        if race_dist <= max_dist:
            plot_min_dist = min(plot_min_dist, race_dist * 0.85)
        if race_dist >= min_dist:
            plot_max_dist = max(plot_max_dist, race_dist * 1.15)

    fig = go.Figure()

    # Anchor for Riegel pace curve: point with best (fastest) pace = max speed
    best_distance = np.nan
    anchor_pace = np.nan

    # Plot Pareto front (red line + circles)
    if not df_pareto.empty:
        pareto_points = list(zip(df_pareto["Distance"], df_pareto["Pace"]))
        pareto_dists, pareto_paces = zip(*sorted(pareto_points, key=lambda x: x[0]))

        if "Speed" in df_pareto.columns:
            max_speed_idx = int(df_pareto["Speed"].idxmax())
            best_distance = float(df_pareto.loc[max_speed_idx, "Distance"])
            anchor_pace = float(df_pareto.loc[max_speed_idx, "Pace"])

        # Riegel pace curve: P(D) = P_anchor * (D/D_anchor)^exponent(D)
        # Derived from T(D) = P(D)*D = P_anchor*D_anchor*(D/D_anchor)^(1+e)
        # → P(D) = P_anchor * (D/D_anchor)^e
        if not np.isnan(anchor_pace) and not np.isnan(best_distance):
            x_vals = np.linspace(plot_min_dist, plot_max_dist, 100).tolist()
            x_vals.append(float(best_distance))
            x_vals = sorted(set(x_vals))

            y_vals = [
                anchor_pace * (d / best_distance) ** riegel_pace_exponent(d)
                for d in x_vals
            ]

            # Ensure curve passes through the anchor point exactly
            anchor_idx = x_vals.index(best_distance)
            y_vals[anchor_idx] = anchor_pace

            best_curve_paces = [seconds_to_pace_string(p) for p in y_vals]
            best_curve_speeds = [
                f"{SECONDS_PER_HOUR / p:.2f} mph" if p and p > 0 else "N/A"
                for p in y_vals
            ]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Best Pace Curve",
                    line=dict(color="black", dash="dash", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Best Pace Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Pace: %{customdata[0]}<br>"
                    + "Speed: %{customdata[1]}<extra></extra>",
                    customdata=list(zip(best_curve_paces, best_curve_speeds)),
                )
            )

        pareto_pace_strs = [seconds_to_pace_string(p) for p in pareto_paces]
        pareto_speed_strs = [
            f"{SECONDS_PER_HOUR / p:.2f} mph" if p and p > 0 else "N/A"
            for p in pareto_paces
        ]

        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_paces),
                mode="lines",
                name="Pareto Front (Best Paces)",
                line=dict(color="red", shape="vh", width=2),
                hovertemplate="<b>Pareto Front</b><extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=list(pareto_dists),
                y=list(pareto_paces),
                mode="markers",
                name="Pareto Points",
                marker=dict(color="red", size=10, symbol="circle"),
                hovertemplate="<b>Pareto Point</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Pace: %{customdata[0]}<br>"
                + "Speed: %{customdata[1]}<extra></extra>",
                customdata=list(zip(pareto_pace_strs, pareto_speed_strs)),
                showlegend=False,
            )
        )

    # Plot targets (green dashed curve + X markers)
    if df_targets is not None and not df_targets.empty:
        target_points = list(zip(df_targets["Distance"], df_targets["Pace"]))
        target_dists, target_paces = zip(*sorted(target_points, key=lambda x: x[0]))

        # Select the "easiest" target curve: highest mean pace (slowest = closest
        # to current Pareto from below on the inverted axis = least effort).
        def curve_score_pace(
            anchor_distance: float, anchor_p: float
        ) -> tuple[list, list, float]:
            sample_points = np.linspace(plot_min_dist, plot_max_dist, 100).tolist()
            sample_points.extend([float(d) for d in target_dists])
            sample_points.append(float(anchor_distance))
            sample_points = sorted(set(sample_points))

            y_curve: list[float] = [
                anchor_p * (d / anchor_distance) ** riegel_pace_exponent(d)
                for d in sample_points
            ]
            mean_pace = float(np.mean(y_curve)) if y_curve else -np.inf
            return sample_points, y_curve, mean_pace

        best_curve: tuple[list, list, float] = ([], [], -np.inf)
        anchor_idx = 0
        for i, (t_dist, t_pace) in enumerate(zip(target_dists, target_paces)):
            x_curve, y_curve, score = curve_score_pace(t_dist, t_pace)
            if score > best_curve[2]:
                best_curve = (x_curve, y_curve, score)
                anchor_idx = i

        x_vals, y_vals, _ = best_curve
        if x_vals:
            anchor_distance = target_dists[anchor_idx]
            anchor_pace_val = target_paces[anchor_idx]
            if anchor_distance in x_vals:
                y_vals[x_vals.index(anchor_distance)] = anchor_pace_val

            target_curve_paces = [seconds_to_pace_string(p) for p in y_vals]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines",
                    name="Target Pace Curve",
                    line=dict(color="green", dash="dashdot", width=2),
                    opacity=0.7,
                    hovertemplate="<b>Target Pace Curve</b><br>"
                    + "Distance: %{x:.2f} mi<br>"
                    + "Pace: %{customdata}<extra></extra>",
                    customdata=target_curve_paces,
                )
            )

        target_pace_strs = [seconds_to_pace_string(p) for p in target_paces]
        target_speed_strs = [
            f"{SECONDS_PER_HOUR / p:.2f} mph" if p and p > 0 else "N/A"
            for p in target_paces
        ]
        fig.add_trace(
            go.Scatter(
                x=list(target_dists),
                y=list(target_paces),
                mode="markers",
                name="Next Targets",
                marker=dict(color="green", size=12, symbol="x"),
                hovertemplate="<b>Target</b><br>"
                + "Distance: %{x:.2f} mi<br>"
                + "Pace: %{customdata[0]}<br>"
                + "Speed: %{customdata[1]}<extra></extra>",
                customdata=list(zip(target_pace_strs, target_speed_strs)),
            )
        )

    # Y-axis range (pace in sec/mile; inverted so faster = visually higher)
    all_paces = []
    if not df_pareto.empty:
        all_paces.extend(df_pareto["Pace"].dropna().tolist())
    if df_targets is not None and not df_targets.empty:
        all_paces.extend(df_targets["Pace"].dropna().tolist())
    y_lo = min(all_paces) * 0.8 if all_paces else 300
    y_hi = max(all_paces) * 1.2 if all_paces else 900

    tick_vals, tick_texts = _pace_axis_ticks(y_lo, y_hi)

    # Race distance vertical lines
    for race_dist, race_label in race_distances:
        if plot_min_dist <= race_dist <= plot_max_dist:
            fig.add_vline(
                x=race_dist,
                line_dash="dot",
                line_color="gray",
                line_width=1,
                opacity=0.6,
            )
            fig.add_annotation(
                x=np.log10(race_dist),
                y=1,
                yref="paper",
                text=race_label,
                showarrow=False,
                font=dict(size=10, color="rgba(150,150,150,0.8)"),
                yanchor="bottom",
                yshift=2,
            )

    fig.update_layout(
        title=(
            f"Pace vs. Distance for {Exercise}<br><sup>Pareto dominance: a point is "
            "kept only if no other point has both longer distance and faster pace; "
            "Riegel curve: pace2 = pace1 \u00d7 (d2/d1)^e, "
            "e\u202f=\u202f0.06\u2013-0.14 (grows with distance).</sup>"
        ),
        xaxis_title="Distance (miles)",
        yaxis_title="Pace (min/mi, upper=faster)",
        xaxis_type="log",
        yaxis_type="log",
        xaxis=dict(range=[np.log10(plot_min_dist), np.log10(plot_max_dist)]),
        yaxis=dict(
            range=[np.log10(y_hi), np.log10(y_lo)],  # inverted: faster pace at top
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_texts,
        ),
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
        height=540,
        margin=dict(t=120, l=60, r=20, b=150),
    )

    return fig


def plot_running_combined(
    df_time_pareto,
    df_time_targets,
    df_pace_pareto,
    df_pace_targets,
    Exercise: str,
):
    """Combined two-row subplot: Total Time vs Distance (top) + Pace vs Distance (bottom).

    The X-axis (distance) is shared between both subplots so that zooming or
    panning on one row automatically updates the other.

    Parameters
    ----------
    df_time_pareto : pd.DataFrame
        Time-Pareto records (from highest_pace_per_distance).
    df_time_targets : pd.DataFrame
        Targets for the time graph.
    df_pace_pareto : pd.DataFrame
        Pace-Pareto records (from highest_pace_per_distance_pace_pareto).
    df_pace_targets : pd.DataFrame
        Targets for the pace graph (computed from pace-Pareto, not time-Pareto).
    Exercise : str
        Exercise to plot.

    Returns
    -------
    plotly.graph_objects.Figure
        Single combined subplot figure.
    """
    from plotly.subplots import make_subplots

    fig_time = plot_running_df(df_time_pareto, df_time_targets, Exercise=Exercise)
    fig_pace = plot_running_pace_df(df_pace_pareto, df_pace_targets, Exercise=Exercise)

    combined = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=["Total Time vs. Distance", "Pace vs. Distance"],
    )

    # Add time traces to row 1
    time_trace_names = {t.name for t in fig_time.data if t.name}
    for trace in fig_time.data:
        combined.add_trace(trace, row=1, col=1)

    # Add pace traces to row 2; suppress legend entries already shown in row 1
    for trace in fig_pace.data:
        if trace.name in time_trace_names:
            trace.showlegend = False
        combined.add_trace(trace, row=2, col=1)

    # Shared x-axis: log scale, label on bottom subplot only
    x_range = list(fig_time.layout.xaxis.range)
    combined.update_xaxes(type="log", range=x_range)
    combined.update_xaxes(title_text="Distance (miles)", row=2, col=1)

    # Row 1 y-axis: total time (log scale, normal orientation — short time at top)
    tl = fig_time.layout
    combined.update_yaxes(
        type="log",
        range=list(tl.yaxis.range),
        title_text="Total Time (min)",
        row=1,
        col=1,
    )

    # Row 2 y-axis: pace (log scale, inverted so faster = visually higher, custom ticks)
    pl = fig_pace.layout
    pace_yaxis_kwargs: dict = dict(
        type="log",
        range=list(pl.yaxis.range),
        title_text="Pace (min/mi)",
    )
    if pl.yaxis.tickmode:
        pace_yaxis_kwargs["tickmode"] = pl.yaxis.tickmode
    if pl.yaxis.tickvals is not None and len(pl.yaxis.tickvals) > 0:
        pace_yaxis_kwargs["tickvals"] = list(pl.yaxis.tickvals)
    if pl.yaxis.ticktext is not None and len(pl.yaxis.ticktext) > 0:
        pace_yaxis_kwargs["ticktext"] = list(pl.yaxis.ticktext)
    combined.update_yaxes(row=2, col=1, **pace_yaxis_kwargs)

    # Race distance vlines on both subplots
    race_distances = [
        (3.10686, "5K"),
        (13.1094, "Half"),
        (26.2188, "Marathon"),
    ]
    x_lo = 10 ** x_range[0]
    x_hi = 10 ** x_range[1]
    for race_dist, race_label in race_distances:
        if x_lo <= race_dist <= x_hi:
            for row in (1, 2):
                combined.add_vline(
                    x=race_dist,
                    line_dash="dot",
                    line_color="gray",
                    line_width=1,
                    opacity=0.6,
                    row=row,
                    col=1,
                )
            combined.add_annotation(
                x=np.log10(race_dist),
                xref="x",
                y=1,
                yref="y domain",
                text=race_label,
                showarrow=False,
                font=dict(size=10, color="rgba(150,150,150,0.8)"),
                yanchor="bottom",
                yshift=2,
                row=1,
                col=1,
            )

    combined.update_layout(
        title=(
            f"Running Performance: {Exercise}<br><sup>"
            "Red\u202f=\u202fPareto front \u00b7 Black\u202f=\u202fBest Riegel curve \u00b7 "
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
                best_pace = SECONDS_PER_HOUR / max_speed if max_speed > 0 else np.nan
                best_distance = pareto_dists[max_speed_idx]

                # Estimate pareto speed at target distance
                if not np.isnan(best_pace):
                    pareto_pace_est = estimate_pace_at_distance(
                        best_pace, best_distance, target_dist
                    )
                    if not np.isnan(pareto_pace_est) and pareto_pace_est > 0:
                        pareto_speed_est = SECONDS_PER_HOUR / pareto_pace_est
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

    # Compute pace Pareto and pace-specific targets for the pace-vs-distance graph.
    # Targets must be computed from the pace-Pareto front (not the time-Pareto)
    # so that the green X markers are positioned correctly relative to the
    # pace-Pareto staircase.
    df_pace_pareto = highest_pace_per_distance_pace_pareto(df)
    df_pace_pareto = add_speed_metric_column(df_pace_pareto)
    df_pace_targets = df_next_running_targets(df_pace_pareto)

    figures_html: dict[str, str] = {}

    exercise_slug = {ex: slugify(ex) for ex in df_records["Exercise"].unique()}

    # Generate a single combined subplot per exercise (time on top, pace on bottom,
    # x-axes linked for synchronized zooming).
    for exercise, slug in exercise_slug.items():
        try:
            exercise_pace_pareto = df_pace_pareto[
                df_pace_pareto["Exercise"] == exercise
            ]
            if not exercise_pace_pareto.empty:
                fig_combined = plot_running_combined(
                    df_records,
                    df_targets,
                    df_pace_pareto,
                    df_pace_targets,
                    Exercise=exercise,
                )
                figures_html[exercise] = plotly_figure_to_html_div(
                    fig_combined, slug, display="block", css_class="running-figure"
                )
            else:
                # Fall back to time-only graph if pace data is unavailable
                fig_time = plot_running_df(df_records, df_targets, Exercise=exercise)
                figures_html[exercise] = plotly_figure_to_html_div(
                    fig_time, slug, display="block", css_class="running-figure"
                )
        except Exception:
            # If plot generation fails, skip this exercise and continue
            plt.close("all")  # Clean up any partial figures

    all_figures_html = "\n".join(figures_html.values())

    # Convert targets to table
    table_html = df_targets_display.to_html(
        classes="display compact cell-border", table_id="runningTable", index=False
    )

    return """
    <div class="content-card">
        <div class="table-wrapper">
            {table_html}
        </div>
    </div>
    <div class="figures-grid">
        {all_figures_html}
    </div>
    """.format(table_html=table_html, all_figures_html=all_figures_html)


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
        padding: clamp(16px, 4vw, 32px);
        background-color: var(--bg);
        color: var(--fg);
        line-height: 1.6;
        max-width: 1200px;
        width: 100%;
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

    .content-card {
        background-color: var(--bg-alt);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 18px;
        box-shadow: var(--shadow);
        margin-bottom: 20px;
        width: min(100%, 1100px);
        margin-left: auto;
        margin-right: auto;
    }

    .figures-grid {
        display: grid;
        gap: clamp(12px, 2vw, 20px);
    }

    @media (min-width: 720px) {
        .figures-grid {
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
        }
    }

    table.dataTable {
        font-size: 14px;
        width: 100% !important;
        min-width: min(720px, 100%);
        word-wrap: break-word;
        background-color: var(--bg-alt);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: 4px;
        overflow: hidden;
        box-shadow: var(--shadow);
        table-layout: auto;
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
        word-break: break-word;
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
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 12px;
        align-items: center;
        margin-bottom: 25px;
        padding: 20px;
        background-color: var(--bg-alt);
        border: 1px solid var(--border);
        border-radius: 4px;
    }

    @media (min-width: 700px) {
        .upload-controls {
            grid-template-columns: minmax(0, 1fr) auto;
        }
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

        .content-card {
            padding: 16px;
        }

        .upload-controls {
            grid-template-columns: minmax(0, 1fr);
        }

        #csvFile,
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

        table.dataTable {
            min-width: 100%;
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
    <div class="content-card">
        <div class="upload-controls">
            <input type="file" id="csvFile" accept=".csv">
            <button id="uploadButton">Upload</button>
            <progress id="uploadProgress" value="0" max="100" style="display:none;"></progress>
        </div>
    </div>
    """

    scripts = """
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize DataTable (jQuery + DataTables are loaded with defer,
        // which executes before DOMContentLoaded fires)
        $('#runningTable').DataTable({
            pageLength: 25,
            responsive: true,
            autoWidth: false,
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
