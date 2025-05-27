import math
import numpy as np
import pandas as pd
from difflib import get_close_matches
import matplotlib.pyplot as plt


def assert_frame_equal(df1, df2):
    assert df1.shape == df2.shape, (
        "DataFrames have different shapes." + f"\n{df1=}\n{df2=}"
    )
    assert sorted(df1.columns) == sorted(df2.columns), (
        "DataFrames have different column names." + f"\n{df1=}\n{df2=}"
    )
    # Ensure column order is the same before sorting rows
    df1_reordered_cols = df1.sort_index(axis=1)
    df2_reordered_cols = df2.sort_index(axis=1)
    # Reset index, sort by all columns, reset index again
    df1_processed = (
        df1_reordered_cols.reset_index(drop=True)
        .sort_values(by=df1_reordered_cols.columns.tolist())
        .reset_index(drop=True)
    )
    df2_processed = (
        df2_reordered_cols.reset_index(drop=True)
        .sort_values(by=df2_reordered_cols.columns.tolist())
        .reset_index(drop=True)
    )
    assert df1_processed.equals(df2_processed), (
        f"\n{df1_processed}\nnot equal to\n{df2_processed}"
    )


def calculate_1rm(weight: float, reps: int) -> float:
    # Input validation
    if (
        weight is None
        or reps is None
        or math.isnan(weight)
        or math.isnan(reps)
        or (reps <= 0)
        or (weight <= 0)
    ):
        # Allow weight == 0 (e.g. bodyweight exercises recorded as 0)
        # but 1RM is meaningless if weight is negative or reps <= 0
        if (weight == 0) and (reps > 0):
            return 0.0  # 1RM for 0 weight is 0
        return np.nan  # Invalid input for calculation

    # If reps is 1, the 1RM is simply the weight lifted.
    if reps == 1:
        return float(weight)

    # Apply the Epley formula
    estimated_1rm = weight * (1 + reps / 30.0)

    return estimated_1rm


def highest_weight_per_rep(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure required columns exist
    required_cols = ["Exercise", "Weight", "Reps"]
    assert all(col in df.columns for col in required_cols)

    # --- Make it simple: Basic Checks and Copy ---
    # Work on a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Convert Weight and Reps to numeric, coercing errors to NaN
    df_copy["Weight"] = pd.to_numeric(df_copy["Weight"], errors="coerce")
    df_copy["Reps"] = pd.to_numeric(df_copy["Reps"], errors="coerce")

    # Drop rows where Weight or Reps are invalid/missing for this calculation
    df_copy = df_copy.dropna(subset=["Exercise", "Weight", "Reps"])

    # Ensure Reps are integers if possible (or handle floats if necessary)
    df_copy["Reps"] = df_copy["Reps"].astype(int)

    if df_copy.empty:
        # Return an empty DataFrame with the original columns structure
        return pd.DataFrame(columns=df.columns)

    # --- Core Logic ---

    # Step 1: Find the row index corresponding to the max weight for each (Exercise, Reps) pair.
    # This handles cases where the same max weight/rep was achieved multiple times,
    # picking one instance (the first one encountered in the original df order by default).
    # Using idxmax ensures we keep the entire row data associated with that max weight.
    idx = df_copy.groupby(["Exercise", "Reps"])["Weight"].idxmax()
    max_weight_sets = df_copy.loc[idx].copy()  # Create df of potential PRs

    # Step 2: Filter based on the superseding rule.
    # A record (W, R) is superseded if there exists another record (W', R') for the same exercise
    # such that R' > R and W' >= W.

    # Define a function to check if a row is superseded within its group
    def is_superseded(row, group_df):
        # Check for rows in the same exercise group
        # with strictly more reps AND greater than or equal weight
        superseding_rows = group_df[
            (group_df["Reps"] > row["Reps"]) & (group_df["Weight"] >= row["Weight"])
        ]
        # Return True if any such row exists (meaning the current row IS superseded)
        return not superseding_rows.empty

    # Apply this check group-wise
    final_record_indices = []
    # Group the potential PRs by exercise
    for exercise_name, group in max_weight_sets.groupby("Exercise"):
        # Apply the check function to each row (axis=1) within the group
        # We want rows where is_superseded is False
        rows_to_keep = group[
            ~group.apply(lambda row: is_superseded(row, group), axis=1)
        ]
        final_record_indices.extend(rows_to_keep.index.tolist())

    # Filter the max_weight_sets DataFrame using the collected indices
    final_df = max_weight_sets.loc[final_record_indices]

    return final_df


def estimate_weight_from_1rm(one_rm: float, reps: int) -> float:
    # Input validation
    if (
        one_rm is None
        or reps is None
        or math.isnan(one_rm)
        or math.isnan(reps)
        or (reps <= 0)
        or (one_rm < 0)
    ):
        if (one_rm == 0) and (reps > 0):
            return 0.0
        return np.nan

    if reps == 1:
        return float(one_rm)

    estimated_weight = one_rm / (1 + reps / 30.0)

    return estimated_weight


def add_1rm_column(df: pd.DataFrame) -> pd.DataFrame:
    # Check if necessary columns exist
    required_cols = ["Weight", "Reps"]
    assert all(col in df.columns for col in required_cols), (
        f"Warning: DataFrame must contain columns: {required_cols} to calculate 1RM. Returning original DataFrame."
    )

    # Work on a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Ensure 'Weight' and 'Reps' are numeric, coercing errors to NaN
    # This prepares the columns for the calculation function
    df_copy["Weight"] = pd.to_numeric(df_copy["Weight"], errors="coerce")
    df_copy["Reps"] = pd.to_numeric(df_copy["Reps"], errors="coerce")

    # Apply the calculate_1rm function row-wise
    # It iterates through rows and passes 'Weight' and 'Reps' to calculate_1rm
    # The result of apply is a Series which becomes the new '1RM' column
    df_copy["1RM"] = df_copy.apply(
        lambda row: calculate_1rm(row["Weight"], row["Reps"]),
        axis=1,  # Apply function row-wise
    )

    # Optional: Round the 1RM column for cleaner presentation
    # df_copy['1RM'] = df_copy['1RM'].round(2)

    return df_copy


def dougs_next_pareto(df_records):
    rows = []
    for ex in df_records["Exercise"].unique():
        ed = df_records[df_records["Exercise"] == ex].sort_values("Reps")
        ws = ed["Weight"].tolist()
        rs = ed["Reps"].tolist()

        # first‐rep side
        rows.append((ex, ws[0] + 5, 1))

        # gaps in the middle
        for i in range(len(rs) - 1):
            if rs[i + 1] > rs[i] + 1:
                nr = rs[i] + 1
                # two candidates: step rep on low, or step weight on high
                c1_w = ws[i]
                c2_w = ws[i + 1] + 5
                rows.append((ex, min(c1_w, c2_w), nr))

        # high‐rep end
        rows.append((ex, ws[-1], rs[-1] + 1))

    return add_1rm_column(pd.DataFrame(rows, columns=["Exercise", "Weight", "Reps"]))


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
