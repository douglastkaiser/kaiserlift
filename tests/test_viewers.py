import math


import pandas as pd

from kaiserlift.df_processers import calculate_1rm
from kaiserlift.viewers import plot_df


def _get_trace(fig, name: str):
    for trace in fig.data:
        if trace.name == name:
            return trace
    raise AssertionError(f"Trace '{name}' not found")


def test_1rm_curves_anchor_to_points():
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Test Lift", "Test Lift"],
            "Weight": [150, 120],
            "Reps": [1, 5],
        }
    )

    df_targets = pd.DataFrame(
        {
            "Exercise": ["Test Lift", "Test Lift"],
            "Weight": [90, 80],
            "Reps": [10, 12],
        }
    )

    fig = plot_df(df_pareto=df_pareto, df_targets=df_targets, Exercise="Test Lift")

    # Verify max achieved 1RM curve intersects Pareto point with highest 1RM
    pareto_one_rms = [
        calculate_1rm(weight, reps)
        for weight, reps in zip(df_pareto["Weight"], df_pareto["Reps"])
    ]
    max_idx = int(pd.Series(pareto_one_rms).idxmax())
    anchor_rep = int(df_pareto.iloc[max_idx]["Reps"])
    anchor_weight = float(df_pareto.iloc[max_idx]["Weight"])

    max_trace = _get_trace(fig, "Max Achieved 1RM")
    max_x = list(max_trace.x)
    assert anchor_rep in max_x
    anchor_pos = max_x.index(anchor_rep)
    assert math.isclose(max_trace.y[anchor_pos], anchor_weight)

    # Verify lowest target 1RM curve intersects weakest target
    target_one_rms = [
        calculate_1rm(weight, reps)
        for weight, reps in zip(df_targets["Weight"], df_targets["Reps"])
    ]
    min_idx = int(pd.Series(target_one_rms).idxmin())
    target_rep = int(df_targets.iloc[min_idx]["Reps"])
    target_weight = float(df_targets.iloc[min_idx]["Weight"])

    target_trace = _get_trace(fig, "Lowest Target 1RM")
    target_x = list(target_trace.x)
    assert target_rep in target_x
    target_pos = target_x.index(target_rep)
    assert math.isclose(target_trace.y[target_pos], target_weight)
