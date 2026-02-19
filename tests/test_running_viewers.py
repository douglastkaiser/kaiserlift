import math

import numpy as np
import pandas as pd

from kaiserlift.running_viewers import plot_running_df
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
