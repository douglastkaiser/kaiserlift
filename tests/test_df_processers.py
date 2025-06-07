# Use pypi installed version of kaiserlift, not local version.
from kaiserlift import (
    calculate_1rm,
    estimate_weight_from_1rm,
    add_1rm_column,
    df_next_pareto,
    highest_weight_per_rep,
    assert_frame_equal,
)
import pandas as pd


def test_assert_frame_equal():
    assert_frame_equal(
        pd.DataFrame({"Weight": [100], "Reps": [1]}),
        pd.DataFrame({"Weight": [100], "Reps": [1]}),
    )

    try:
        assert_frame_equal(
            pd.DataFrame({"Weight": [100], "Reps": [1]}),
            pd.DataFrame({"Weight": [100], "Reps": [2]}),
        )
    except AssertionError as e:
        assert "not equal to" in f"{e}"


def test_calculate_1rm():
    assert calculate_1rm(100, 1) == 100.0
    assert calculate_1rm(1, 15) == 1.5


def test_highest_weight_per_rep():
    # Should be the same for 100x1 only.
    assert_frame_equal(
        highest_weight_per_rep(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100],
                    "Reps": [1],
                }
            )
        ),
        pd.DataFrame(
            {
                "Exercise": "Bench Press",
                "Weight": [100],
                "Reps": [1],
            }
        ),
    )

    # Fake out, 90x5 should be dropped in favor of 100x10
    assert_frame_equal(
        highest_weight_per_rep(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100, 90],
                    "Reps": [10, 5],
                }
            )
        ),
        pd.DataFrame(
            {
                "Exercise": "Bench Press",
                "Weight": [100],
                "Reps": [10],
            }
        ),
    )

    # Real now, 90x15, 110x1, and 100x10 will be kept, all others dropped.
    assert_frame_equal(
        highest_weight_per_rep(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100, 90, 100, 95, 110],
                    "Reps": [10, 15, 5, 3, 1],
                }
            )
        ),
        pd.DataFrame(
            {
                "Exercise": "Bench Press",
                "Weight": [100, 90, 110],
                "Reps": [10, 15, 1],
            }
        ),
    )


def test_estimate_weight_from_1rm():
    assert estimate_weight_from_1rm(200, 1) == 200.0
    assert estimate_weight_from_1rm(200, 4) == 176.47058823529412


def test_calculate_1rm_from_estimate():
    assert calculate_1rm(estimate_weight_from_1rm(200, 4), 4) == 200.0


def test_add_1rm_column():
    # Should be the same for 100x1 only.
    assert_frame_equal(
        add_1rm_column(
            pd.DataFrame(
                {
                    "Weight": [100],
                    "Reps": [1],
                }
            )
        ),
        pd.DataFrame(
            {
                "Weight": [100],
                "Reps": [1],
                "1RM": [100.0],
            }
        ),
    )

    # More real values. w*(1+r/30.0)
    assert_frame_equal(
        add_1rm_column(
            pd.DataFrame(
                {
                    "Weight": [100, 1, 13],
                    "Reps": [30, 15, 1],
                }
            )
        ),
        pd.DataFrame(
            {
                "Weight": [100, 1, 13],
                "Reps": [30, 15, 1],
                "1RM": [200.0, 1.5, 13.0],
            }
        ),
    )


def test_df_next_pareto():
    # Simple case for 100x1; 105x1 and 100x2
    assert_frame_equal(
        df_next_pareto(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100],
                    "Reps": [1],
                }
            )
        ),
        add_1rm_column(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [105, 100],
                    "Reps": [1, 2],
                }
            )
        ),
    )

    assert_frame_equal(
        df_next_pareto(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100],
                    "Reps": [5],
                }
            )
        ),
        add_1rm_column(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [105, 100],
                    "Reps": [1, 6],
                }
            )
        ),
    )

    # Two excersice test
    assert_frame_equal(
        df_next_pareto(
            pd.DataFrame(
                {
                    "Exercise": ["Bench Press"] + ["Incline Bench Press"] * 2,
                    "Weight": [100] + [80, 50],
                    "Reps": [5] + [1, 10],
                }
            )
        ),
        add_1rm_column(
            pd.DataFrame(
                {
                    "Exercise": ["Bench Press"] * 2 + ["Incline Bench Press"] * 3,
                    "Weight": [105, 100] + [85, 55, 50],
                    "Reps": [1, 6] + [1, 2, 11],
                }
            )
        ),
    )

    # Okay the big case now. Lowest next set on the pareto front.
    # First entry not on rep 1
    # Gaps in both rep and weight
    # Single increment off example (80x5 and 75x6)
    assert_frame_equal(
        df_next_pareto(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [100, 80, 75, 50],
                    "Reps": [2, 5, 6, 10],
                }
            )
        ),
        add_1rm_column(
            pd.DataFrame(
                {
                    "Exercise": "Bench Press",
                    "Weight": [105, 85, 55, 50],
                    "Reps": [1, 3, 7, 11],
                }
            )
        ),
    )
