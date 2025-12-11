import math

import pandas as pd

from kaiserlift.running_processers import estimate_pace_at_distance
from kaiserlift.running_viewers import plot_running_df


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

    # Verify best speed curve intersects Pareto point with max speed
    max_idx = int(df_pareto["Speed"].idxmax())
    anchor_distance = float(df_pareto.iloc[max_idx]["Distance"])
    anchor_speed = float(df_pareto.iloc[max_idx]["Speed"])

    best_trace = _get_trace(fig, "Best Speed Curve")
    best_x = list(best_trace.x)
    assert anchor_distance in best_x
    anchor_pos = best_x.index(anchor_distance)
    assert math.isclose(best_trace.y[anchor_pos], anchor_speed)

    # Verify target speed curve intersects the selected target point
    best_pace = 3600 / anchor_speed
    furthest_below_idx = 0
    max_distance_below = -float("inf")
    for i, (t_dist, t_speed) in enumerate(
        zip(df_targets["Distance"], df_targets["Speed"])
    ):
        pareto_pace_est = estimate_pace_at_distance(best_pace, anchor_distance, t_dist)
        if not math.isnan(pareto_pace_est) and pareto_pace_est > 0:
            pareto_speed_est = 3600 / pareto_pace_est
            distance_below = pareto_speed_est - t_speed
            if distance_below > max_distance_below:
                max_distance_below = distance_below
                furthest_below_idx = i

    target_anchor_distance = float(df_targets.iloc[furthest_below_idx]["Distance"])
    target_anchor_speed = float(df_targets.iloc[furthest_below_idx]["Speed"])

    target_trace = _get_trace(fig, "Target Speed Curve")
    target_x = list(target_trace.x)
    assert target_anchor_distance in target_x
    target_pos = target_x.index(target_anchor_distance)
    assert math.isclose(target_trace.y[target_pos], target_anchor_speed)
