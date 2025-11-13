"""Tests for running data processing functions."""

import pandas as pd
import numpy as np
from datetime import datetime

from kaiserlift.running_processers import (
    calculate_pace_from_duration,
    seconds_to_pace_string,
    highest_pace_per_distance,
    estimate_pace_at_distance,
    df_next_running_targets,
    add_speed_metric_column,
    predict_race_pace,
)


def test_calculate_pace_from_duration():
    """Test pace calculation from duration and distance."""
    # 27.0 minutes for 3.0 miles = 9:00 per mile = 540 seconds/mile
    assert calculate_pace_from_duration(27.0, 3.0) == 540.0
    # 47.5 minutes for 5.0 miles = 9:30 per mile = 570 seconds/mile
    assert calculate_pace_from_duration(47.5, 5.0) == 570.0
    # 60.0 minutes for 6.0 miles = 10:00 per mile = 600 seconds/mile
    assert calculate_pace_from_duration(60.0, 6.0) == 600.0
    # Edge cases
    assert np.isnan(calculate_pace_from_duration(np.nan, 5.0))
    assert np.isnan(calculate_pace_from_duration(30.0, np.nan))
    assert np.isnan(calculate_pace_from_duration(30.0, 0))  # Zero distance


def test_seconds_to_pace_string():
    """Test pace string formatting."""
    assert seconds_to_pace_string(570) == "9:30"
    assert seconds_to_pace_string(525) == "8:45"
    assert seconds_to_pace_string(600) == "10:00"
    assert seconds_to_pace_string(435) == "7:15"
    assert np.isnan(seconds_to_pace_string(0))
    assert np.isnan(seconds_to_pace_string(-10))
    assert np.isnan(seconds_to_pace_string(np.nan))


def test_highest_pace_per_distance():
    """Test Pareto front extraction for running data."""
    df = pd.DataFrame(
        {
            "Date": [datetime(2024, 1, 15)] * 4,
            "Exercise": ["Running"] * 4,
            "Category": ["Cardio"] * 4,
            "Distance": [5.0, 5.0, 10.0, 3.0],
            "Pace": [600, 570, 600, 540],  # 10:00, 9:30, 10:00, 9:00
        }
    )

    result = highest_pace_per_distance(df)

    # All three distances are on the Pareto front:
    # 3.0 @ 540 (9:00) - fastest pace
    # 5.0 @ 570 (9:30) - middle distance
    # 10.0 @ 600 (10:00) - longest distance
    # None is dominated because no record has both longer distance AND faster pace
    assert len(result) == 3
    assert result.loc[result["Distance"] == 3.0, "Pace"].values[0] == 540
    assert result.loc[result["Distance"] == 5.0, "Pace"].values[0] == 570
    assert result.loc[result["Distance"] == 10.0, "Pace"].values[0] == 600


def test_highest_pace_per_distance_pareto_dominance():
    """Test that Pareto dominance is correctly applied."""
    # Create a scenario where we have clear dominance
    df = pd.DataFrame(
        {
            "Date": [datetime(2024, 1, i) for i in range(1, 6)],
            "Exercise": ["Running"] * 5,
            "Category": ["Cardio"] * 5,
            "Distance": [3.0, 5.0, 7.0, 10.0, 13.1],
            "Pace": [540, 570, 600, 630, 660],  # Pace getting slower with distance
        }
    )

    result = highest_pace_per_distance(df)

    # All should be on the Pareto front (longer distance, slower pace is OK)
    assert len(result) == 5


def test_highest_pace_per_distance_dominated():
    """Test that dominated records are removed."""
    df = pd.DataFrame(
        {
            "Date": [datetime(2024, 1, i) for i in range(1, 4)],
            "Exercise": ["Running"] * 3,
            "Category": ["Cardio"] * 3,
            "Distance": [5.0, 10.0, 5.0],
            "Pace": [600, 570, 630],  # 10:00, 9:30, 10:30
        }
    )

    result = highest_pace_per_distance(df)

    # 10.0 @ 9:30 dominates both 5.0 mile runs
    # So only 10.0 @ 9:30 should remain
    assert len(result) == 1
    assert result["Distance"].values[0] == 10.0
    assert result["Pace"].values[0] == 570


def test_estimate_pace_at_distance():
    """Test pace estimation at different distances using Riegel's formula."""
    # Best pace: 9:30 (570 sec/mi) at 5 miles
    # Estimate at 10 miles (2x distance)
    # Riegel's formula: pace2 = pace1 * (distance2/distance1)^0.06
    # 570 * (10/5)^0.06 = 570 * 2^0.06 ≈ 594.05
    estimated = estimate_pace_at_distance(570, 5.0, 10.0)
    expected = 570 * (10.0 / 5.0) ** 0.06  # Riegel's formula
    assert abs(estimated - expected) < 0.1

    # Same distance should return same pace
    estimated = estimate_pace_at_distance(570, 5.0, 5.0)
    assert estimated == 570

    # Shorter distance should be faster
    estimated = estimate_pace_at_distance(570, 5.0, 2.5)
    assert estimated < 570


def test_estimate_pace_at_distance_edge_cases():
    """Test edge cases for pace estimation."""
    # Zero distance
    assert np.isnan(estimate_pace_at_distance(570, 0, 5.0))
    assert np.isnan(estimate_pace_at_distance(570, 5.0, 0))

    # NaN pace
    assert np.isnan(estimate_pace_at_distance(np.nan, 5.0, 10.0))


def test_add_speed_metric_column():
    """Test speed calculation from pace."""
    df = pd.DataFrame(
        {
            "Distance": [5.0, 10.0],
            "Pace": [600, 570],  # 10:00 and 9:30 pace
        }
    )

    result = add_speed_metric_column(df)

    # Speed (mph) = 3600 / pace (sec/mi)
    # 10:00 pace = 600 sec/mi = 6.0 mph
    # 9:30 pace = 570 sec/mi = 6.316 mph
    assert "Speed" in result.columns
    assert abs(result.loc[0, "Speed"] - 6.0) < 0.01
    assert abs(result.loc[1, "Speed"] - 6.316) < 0.01


def test_df_next_running_targets():
    """Test target generation from Pareto front."""
    df_records = pd.DataFrame(
        {
            "Exercise": ["Running"] * 2,
            "Distance": [5.0, 10.0],
            "Pace": [570, 600],  # 9:30 and 10:00
        }
    )

    targets = df_next_running_targets(df_records)

    # Should have at least:
    # 1. Faster pace at 5.0 miles (570 * 0.98 = 558.6)
    # 2. Gap filler(s) between 5.0 and 10.0
    # 3. Longer distance at 11.0 miles (10.0 is in 5-13 range, so +1 mile)
    assert len(targets) >= 3
    assert "Speed" in targets.columns

    # Check shortest distance target (2% improvement)
    shortest_target = targets[targets["Distance"] == 5.0]
    assert len(shortest_target) == 1
    assert abs(shortest_target["Pace"].values[0] - 570 * 0.98) < 0.1

    # Check longest distance target (+1.0 mile for 5-13 mile range)
    longest_target = targets[targets["Distance"] == 11.0]
    assert len(longest_target) == 1
    assert longest_target["Pace"].values[0] == 600


def test_df_next_running_targets_gap_filling():
    """Test that gap fillers are created for large distance gaps."""
    df_records = pd.DataFrame(
        {
            "Exercise": ["Running"] * 2,
            "Distance": [3.0, 10.0],  # Large gap
            "Pace": [540, 600],
        }
    )

    targets = df_next_running_targets(df_records)

    # Should have multiple gap fillers (0.5 mi increments)
    gap_fillers = targets[(targets["Distance"] > 3.0) & (targets["Distance"] < 10.0)]
    assert len(gap_fillers) > 0


def test_df_next_running_targets_empty():
    """Test target generation with empty input."""
    df_records = pd.DataFrame(
        {
            "Exercise": [],
            "Distance": [],
            "Pace": [],
        }
    )

    targets = df_next_running_targets(df_records)
    assert len(targets) == 0


def test_predict_race_pace():
    """Test race pace prediction."""
    df_records = pd.DataFrame(
        {
            "Exercise": ["Running"] * 3,
            "Distance": [3.0, 5.0, 10.0],
            "Pace": [540, 570, 600],  # 9:00, 9:30, 10:00
        }
    )

    # Predict 5K (3.1 miles) pace
    prediction = predict_race_pace(df_records, "Running", 3.1)

    assert "optimistic_pace" in prediction
    assert "conservative_pace" in prediction
    assert "optimistic_time" in prediction
    assert "conservative_time" in prediction

    # Optimistic should be based on interpolation from 3.0 mile PR
    assert not np.isnan(prediction["optimistic_pace"])
    assert not np.isnan(prediction["conservative_pace"])

    # Conservative should be slower than optimistic
    assert prediction["conservative_pace"] >= prediction["optimistic_pace"]


def test_predict_race_pace_no_data():
    """Test race pace prediction with no matching exercise."""
    df_records = pd.DataFrame(
        {
            "Exercise": ["Running"],
            "Distance": [5.0],
            "Pace": [570],
        }
    )

    prediction = predict_race_pace(df_records, "NonExistent", 5.0)

    assert np.isnan(prediction["optimistic_pace"])
    assert np.isnan(prediction["conservative_pace"])
    assert prediction["optimistic_time"] == "N/A"
    assert prediction["conservative_time"] == "N/A"


def test_multiple_exercises():
    """Test handling of multiple exercise types."""
    df = pd.DataFrame(
        {
            "Date": [datetime(2024, 1, 1)] * 4,
            "Exercise": ["Running", "Running", "Cycling", "Cycling"],
            "Category": ["Cardio"] * 4,
            "Distance": [5.0, 10.0, 10.0, 20.0],
            "Pace": [570, 600, 300, 330],
        }
    )

    result = highest_pace_per_distance(df)

    # Should have records for both exercises
    assert "Running" in result["Exercise"].values
    assert "Cycling" in result["Exercise"].values

    # Each exercise should have its own Pareto front
    running_records = result[result["Exercise"] == "Running"]
    cycling_records = result[result["Exercise"] == "Cycling"]

    assert len(running_records) == 2
    assert len(cycling_records) == 2


def test_running_targets_multiple_exercises():
    """Test target generation for multiple exercises."""
    df_records = pd.DataFrame(
        {
            "Exercise": ["Running", "Running", "Cycling", "Cycling"],
            "Distance": [5.0, 10.0, 10.0, 20.0],
            "Pace": [570, 600, 300, 330],
        }
    )

    targets = df_next_running_targets(df_records)

    # Should have targets for both exercises
    assert "Running" in targets["Exercise"].values
    assert "Cycling" in targets["Exercise"].values
