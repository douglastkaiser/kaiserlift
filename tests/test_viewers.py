import math

import pandas as pd

from kaiserlift.df_processers import calculate_1rm
from kaiserlift.viewers import plot_df, plot_df_1rm


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


def test_1rm_graph_best_1rm_line_at_max():
    """1RM graph: best-1RM reference line is at the maximum 1RM across Pareto."""
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Test Lift", "Test Lift"],
            "Weight": [150.0, 100.0],
            "Reps": [1, 10],
            "1RM": [150.0, 130.0],  # pre-computed for clarity
        }
    )

    fig = plot_df_1rm(df_pareto=df_pareto, Exercise="Test Lift")

    best_trace = _get_trace(fig, "Best 1RM")
    # The horizontal line should sit at max(1RM values) = 150
    assert all(math.isclose(v, 150.0) for v in best_trace.y)


def test_1rm_graph_pareto_staircase_non_increasing():
    """1RM graph: a valid 1RM Pareto front has non-increasing 1RM as reps rise.

    When the input is a properly filtered 1RM Pareto front (e.g., from
    highest_1rm_per_rep), each successive record at higher reps must have
    a strictly lower 1RM — otherwise the lower-rep record would have been
    dominated and removed.  The staircase therefore steps downward to the
    right, mirroring the weight-vs-reps graph.
    """
    # 1RM = W * (1 + (R-1)/30):  150 → 136 → 130  — strictly decreasing.
    # All three survive the 1RM Pareto because no higher-rep record beats any
    # lower-rep record's 1RM.
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Test Lift"] * 3,
            "Weight": [150.0, 120.0, 100.0],
            "Reps": [1, 5, 10],
            "1RM": [150.0, 136.0, 130.0],
        }
    )

    fig = plot_df_1rm(df_pareto=df_pareto, Exercise="Test Lift")

    pareto_trace = _get_trace(fig, "Pareto Front (1RM)")
    reps = list(pareto_trace.x)
    one_rms = list(pareto_trace.y)
    # Sort by reps and verify 1RM is non-increasing (decreasing as reps grow)
    sorted_pairs = sorted(zip(reps, one_rms))
    one_rms_sorted = [p[1] for p in sorted_pairs]
    for i in range(len(one_rms_sorted) - 1):
        assert one_rms_sorted[i] >= one_rms_sorted[i + 1]


def test_1rm_graph_target_line_at_min_target_1rm():
    """1RM graph: lowest-target reference line sits at the minimum target 1RM."""
    df_pareto = pd.DataFrame(
        {
            "Exercise": ["Test Lift"],
            "Weight": [150.0],
            "Reps": [1],
            "1RM": [150.0],
        }
    )

    df_targets = pd.DataFrame(
        {
            "Exercise": ["Test Lift", "Test Lift"],
            "Weight": [90.0, 80.0],
            "Reps": [10, 12],
        }
    )

    fig = plot_df_1rm(df_pareto=df_pareto, df_targets=df_targets, Exercise="Test Lift")

    target_1rms = [
        calculate_1rm(w, r) for w, r in zip(df_targets["Weight"], df_targets["Reps"])
    ]
    expected_min = min(target_1rms)

    target_line = _get_trace(fig, "Lowest Target 1RM")
    assert all(math.isclose(v, expected_min) for v in target_line.y)
