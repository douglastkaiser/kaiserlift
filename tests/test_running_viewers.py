import math

import numpy as np
import pandas as pd

from kaiserlift.running_viewers import plot_running_df, plot_running_pace_df
from kaiserlift.running_processers import riegel_pace_exponent


def _get_trace(fig, name: str):
    for trace in fig.data:
        if trace.name == name:
            return trace
    raise AssertionError(f"Trace '{name}' not found")


def test_running_curves_anchor_to_points():
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Run", "Run"],
            "Distance": [1.0, 5.0],
            "Speed": [10.0, 8.0],
        }
    )

    df_targets = pd.DataFrame(
        {
            "Exercise": ["Run", "Run"],
            "Distance": [3.0, 6.0],
            "Speed": [7.0, 6.5],
        }
    )

    fig = plot_running_df(df_pareto=df_pareto, df_targets=df_targets, Exercise="Run")

    # Verify best time curve intersects the Pareto point with max speed (best pace).
    # Duration = distance / speed * 60  (speed in mph → duration in minutes)
    max_idx = int(df_pareto["Speed"].idxmax())
    anchor_distance = float(df_pareto.iloc[max_idx]["Distance"])
    anchor_speed = float(df_pareto.iloc[max_idx]["Speed"])
    anchor_duration = anchor_distance / anchor_speed * 60.0  # minutes

    best_trace = _get_trace(fig, "Best Time Curve")
    best_x = list(best_trace.x)
    assert anchor_distance in best_x
    anchor_pos = best_x.index(anchor_distance)
    assert math.isclose(best_trace.y[anchor_pos], anchor_duration)

    # Verify target time curve intersects the selected target anchor.
    # The "easiest" target is the one whose Riegel curve has the highest mean
    # time (highest = slowest = least improvement required).
    target_durations = [
        d / s * 60.0 for d, s in zip(df_targets["Distance"], df_targets["Speed"])
    ]

    best_score = -np.inf
    best_target_idx = 0
    sample = np.linspace(0.5, 10.0, 50).tolist()
    for i, (t_dist, t_dur) in enumerate(zip(df_targets["Distance"], target_durations)):
        times = [t_dur * (d / t_dist) ** (1 + riegel_pace_exponent(d)) for d in sample]
        mean_t = float(np.mean(times))
        if mean_t > best_score:
            best_score = mean_t
            best_target_idx = i

    target_anchor_distance = float(df_targets.iloc[best_target_idx]["Distance"])
    target_anchor_duration = target_durations[best_target_idx]

    target_trace = _get_trace(fig, "Target Time Curve")
    target_x = list(target_trace.x)
    assert target_anchor_distance in target_x
    target_pos = target_x.index(target_anchor_distance)
    assert math.isclose(target_trace.y[target_pos], target_anchor_duration)


def test_pace_graph_best_curve_anchors_to_pareto():
    """Pace graph: best-pace curve intersects the fastest-pace Pareto point."""
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Run", "Run"],
            "Distance": [1.0, 5.0],
            "Pace": [480.0, 540.0],  # 8:00 and 9:00 (1-mile is faster)
            "Speed": [7.5, 6.667],
        }
    )

    fig = plot_running_pace_df(df_pareto=df_pareto, Exercise="Run")

    # Anchor = max-speed point = 1-mile (pace 480)
    best_trace = _get_trace(fig, "Best Pace Curve")
    best_x = list(best_trace.x)
    assert 1.0 in best_x
    anchor_pos = best_x.index(1.0)
    assert math.isclose(best_trace.y[anchor_pos], 480.0)


def test_pace_graph_riegel_curve_uses_pace_exponent():
    """Pace graph: curve follows P(D) = P_anchor * (D/D_anchor)^e, not (1+e)."""
    anchor_pace = 480.0  # 8:00/mi
    anchor_dist = 1.0

    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Run"],
            "Distance": [anchor_dist],
            "Pace": [anchor_pace],
            "Speed": [7.5],
        }
    )

    fig = plot_running_pace_df(df_pareto=df_pareto, Exercise="Run")

    best_trace = _get_trace(fig, "Best Pace Curve")
    x_vals = list(best_trace.x)
    y_vals = list(best_trace.y)

    # Pick an arbitrary test distance away from the anchor
    test_dist = 5.0
    if test_dist in x_vals:
        idx = x_vals.index(test_dist)
        expected = anchor_pace * (test_dist / anchor_dist) ** riegel_pace_exponent(
            test_dist
        )
        assert math.isclose(y_vals[idx], expected, rel_tol=1e-6)


def test_pace_graph_target_curve_anchors_to_easiest_target():
    """Pace graph: target-pace curve intersects the slowest (easiest) target."""
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Run"],
            "Distance": [3.0],
            "Pace": [540.0],
            "Speed": [6.667],
        }
    )

    # Two targets: the one at greater distance will have higher mean pace (easier)
    df_targets = pd.DataFrame(
        {
            "Exercise": ["Run", "Run"],
            "Distance": [4.0, 6.0],
            "Pace": [555.0, 575.0],
            "Speed": [6.486, 6.261],
        }
    )

    fig = plot_running_pace_df(
        df_pareto=df_pareto, df_targets=df_targets, Exercise="Run"
    )

    # Determine which target is the "easiest" (highest mean pace curve)
    sample = np.linspace(0.5, 10.0, 50).tolist()
    best_score = -np.inf
    best_anchor_dist = None
    best_anchor_pace = None
    for t_dist, t_pace in zip(df_targets["Distance"], df_targets["Pace"]):
        paces = [t_pace * (d / t_dist) ** riegel_pace_exponent(d) for d in sample]
        score = float(np.mean(paces))
        if score > best_score:
            best_score = score
            best_anchor_dist = float(t_dist)
            best_anchor_pace = float(t_pace)

    target_trace = _get_trace(fig, "Target Pace Curve")
    target_x = list(target_trace.x)
    assert best_anchor_dist in target_x
    anchor_pos = target_x.index(best_anchor_dist)
    assert math.isclose(target_trace.y[anchor_pos], best_anchor_pace)
