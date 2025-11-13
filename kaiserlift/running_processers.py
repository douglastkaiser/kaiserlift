"""Running data processing module for KaiserLift.

This module provides functionality for processing running/cardio data,
calculating pace metrics, and generating training targets based on
Pareto front analysis.
"""

import os
from pathlib import Path
from typing import IO, Iterable

import numpy as np
import pandas as pd


def calculate_pace_from_duration(
    duration_minutes: float, distance_miles: float
) -> float:
    """Calculate pace in seconds per mile from duration and distance.

    Parameters
    ----------
    duration_minutes : float
        Total duration of run in minutes
    distance_miles : float
        Total distance in miles

    Returns
    -------
    float
        Pace in seconds per mile

    Examples
    --------
    >>> calculate_pace_from_duration(27.0, 3.0)
    540.0
    >>> calculate_pace_from_duration(47.5, 5.0)
    570.0
    """
    if pd.isna(duration_minutes) or pd.isna(distance_miles) or distance_miles <= 0:
        return np.nan
    try:
        # Convert duration from minutes to seconds, then divide by distance
        pace_seconds_per_mile = (duration_minutes * 60) / distance_miles
        return pace_seconds_per_mile
    except (ValueError, ZeroDivisionError):
        return np.nan


def seconds_to_pace_string(seconds: float) -> str:
    """Convert seconds/mile to 'M:SS' format.

    Parameters
    ----------
    seconds : float
        Pace in seconds per mile

    Returns
    -------
    str
        Pace formatted as 'M:SS'

    Examples
    --------
    >>> seconds_to_pace_string(570)
    '9:30'
    >>> seconds_to_pace_string(525)
    '8:45'
    """
    if pd.isna(seconds) or seconds <= 0:
        return np.nan
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def process_running_csv_files(files: Iterable[IO | Path]) -> pd.DataFrame:
    """Load and clean running data from CSV files.

    Parameters
    ----------
    files:
        Iterable of file paths or file-like objects. Uses the last file
        or most recently created file if multiple paths provided.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: [Date, Exercise, Category, Distance, Pace]
        Pace is calculated from Duration and Distance and returned in seconds/mile.
        Distance in miles.
    """

    file_list = list(files)
    if not file_list:
        raise ValueError("No CSV files provided")

    def _is_pathlike(obj: object) -> bool:
        return isinstance(obj, (str, os.PathLike))

    if all(_is_pathlike(f) for f in file_list):
        latest_file = max(file_list, key=os.path.getctime)
        print(f"Using {latest_file}")
        data_source = latest_file
    else:
        data_source = file_list[-1]

    df = pd.read_csv(data_source)
    df.columns = df.columns.str.strip()

    # Handle distance and duration column variants (e.g., "Distance (miles)", "Duration (minutes)")
    distance_like = next((c for c in df.columns if c.startswith("Distance (")), None)
    if distance_like and "Distance" not in df.columns:
        df = df.rename(columns={distance_like: "Distance"})

    duration_like = next((c for c in df.columns if c.startswith("Duration (")), None)
    if duration_like and "Duration" not in df.columns:
        df = df.rename(columns={duration_like: "Duration"})

    # Parse date
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df_sorted = df.sort_values(by="Date", ascending=True)

    # Ensure numeric types for Distance and Duration
    df_sorted["Distance"] = pd.to_numeric(
        df_sorted.get("Distance", np.nan), errors="coerce"
    )
    df_sorted["Duration"] = pd.to_numeric(
        df_sorted.get("Duration", np.nan), errors="coerce"
    )

    # Calculate pace from Duration (minutes) and Distance (miles)
    df_sorted["Pace"] = df_sorted.apply(
        lambda row: calculate_pace_from_duration(
            row.get("Duration", np.nan), row.get("Distance", np.nan)
        ),
        axis=1,
    )

    # Filter to only Cardio category
    df_sorted = df_sorted[df_sorted["Category"] == "Cardio"]

    # Drop unused columns (Duration is dropped after calculating Pace)
    df_sorted = df_sorted.drop(
        [
            "Distance Unit",
            "Duration Unit",
            "Duration",
            "Time",
            "Weight",
            "Reps",
            "Weight Unit",
        ],
        axis=1,
        errors="ignore",
    )

    # Ensure required columns exist
    for col in ["Distance", "Pace"]:
        if col not in df_sorted.columns:
            df_sorted[col] = np.nan

    return df_sorted[["Date", "Exercise", "Category", "Distance", "Pace"]].dropna(
        subset=["Distance", "Pace"]
    )


def highest_pace_per_distance(df: pd.DataFrame) -> pd.DataFrame:
    """Find best (fastest) pace for each distance using Pareto dominance.

    Groups by (Exercise, Distance) and finds minimum pace (lower = faster).
    Applies Pareto dominance filter: removes records that are dominated
    by others (longer distance with same or faster pace).

    Parameters
    ----------
    df : pd.DataFrame
        Running data with columns: [Date, Exercise, Category, Distance, Pace]

    Returns
    -------
    pd.DataFrame
        Pareto records representing true running PRs

    Notes
    -----
    A record (D, P) is dominated if there exists another record (D', P') where:
    - D' >= D (at least as far)
    - P' <= P (at least as fast, i.e., lower pace)
    """

    df_copy = df.copy()
    df_copy["Distance"] = pd.to_numeric(df_copy["Distance"], errors="coerce")
    df_copy["Pace"] = pd.to_numeric(df_copy["Pace"], errors="coerce")
    df_copy = df_copy.dropna(subset=["Exercise", "Distance", "Pace"])

    if df_copy.empty:
        return pd.DataFrame(columns=df.columns)

    # Find fastest pace (minimum) for each (Exercise, Distance) pair
    idx = df_copy.groupby(["Exercise", "Distance"])["Pace"].idxmin()
    best_pace_sets = df_copy.loc[idx].copy()

    # Apply Pareto dominance filter
    def is_dominated(row, group_df):
        """Check if this running record is dominated.

        Record (D, P) is dominated if exists (D', P') where:
        - D' >= D (at least as far)
        - P' <= P (at least as fast)
        """
        dominating = group_df[
            (group_df["Distance"] >= row["Distance"])
            & (group_df["Pace"] <= row["Pace"])
        ]
        # More than just itself means it's dominated
        return len(dominating) > 1

    final_indices = []
    for exercise_name, group in best_pace_sets.groupby("Exercise"):
        rows_to_keep = group[~group.apply(lambda row: is_dominated(row, group), axis=1)]
        final_indices.extend(rows_to_keep.index.tolist())

    return best_pace_sets.loc[final_indices].sort_values(["Exercise", "Distance"])


def estimate_pace_at_distance(
    best_pace: float, best_distance: float, target_distance: float
) -> float:
    """Estimate pace at different distance using Riegel's formula.

    Riegel's formula is the standard in running performance prediction.
    Based on the power law: T2 = T1 * (D2/D1)^1.06
    For pace: pace2 = pace1 * (D2/D1)^0.06

    Parameters
    ----------
    best_pace : float
        Best known pace in seconds/mile
    best_distance : float
        Distance at which best_pace was achieved (miles)
    target_distance : float
        Distance to estimate pace for (miles)

    Returns
    -------
    float
        Estimated pace in seconds/mile at target distance

    Examples
    --------
    >>> estimate_pace_at_distance(570, 5.0, 10.0)  # Double distance
    596.7  # Predicted slower pace using Riegel's formula
    """

    if best_distance <= 0 or target_distance <= 0 or pd.isna(best_pace):
        return np.nan

    if target_distance == best_distance:
        return float(best_pace)

    # Riegel's formula: pace increases by (distance_ratio)^0.06
    distance_ratio = target_distance / best_distance
    pace_factor = distance_ratio**0.06

    estimated_pace = best_pace * pace_factor
    return estimated_pace


def add_speed_metric_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'Speed' column in mph for easier interpretation.

    Converts pace (sec/mi) to speed (mph) using: speed = 3600 / pace

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'Pace' column in seconds/mile

    Returns
    -------
    pd.DataFrame
        DataFrame with additional 'Speed' column in mph
    """

    df_copy = df.copy()
    df_copy["Distance"] = pd.to_numeric(df_copy["Distance"], errors="coerce")
    df_copy["Pace"] = pd.to_numeric(df_copy["Pace"], errors="coerce")

    # Convert pace (sec/mi) to speed (mph)
    # 1 hour = 3600 seconds
    # speed (mph) = 3600 / pace (sec/mi)
    df_copy["Speed"] = df_copy["Pace"].apply(
        lambda p: 3600 / p if pd.notna(p) and p > 0 else np.nan
    )

    return df_copy


def df_next_running_targets(df_records: pd.DataFrame) -> pd.DataFrame:
    """Generate next achievable running targets based on Pareto front.

    For each exercise, generates three types of targets:
    1. Shortest distance target: 2% faster at minimum distance
    2. Gap fillers: distances between existing Pareto points (0.5 mi increments)
    3. Longest distance target: variable increment based on distance
       - Under 5 miles: +0.5 miles
       - 5-13 miles: +1 mile
       - 13+ miles: +10%

    Parameters
    ----------
    df_records : pd.DataFrame
        Pareto running records with columns: [Exercise, Distance, Pace]

    Returns
    -------
    pd.DataFrame
        Target runs with columns: [Exercise, Distance, Pace, Speed]

    Examples
    --------
    Given PRs at 5.0 mi @ 9:30 and 10.0 mi @ 10:00, generates:
    - 5.0 mi @ 9:18 (2% faster at short distance)
    - 5.5 mi @ estimated pace (gap filler)
    - ... more gap fillers up to 10.0 mi
    - 11.0 mi @ 10:00 (extend longest distance by 1 mile)
    """

    rows = []

    for ex in df_records["Exercise"].unique():
        ed = df_records[df_records["Exercise"] == ex].sort_values("Distance")

        if ed.empty:
            continue

        distances = ed["Distance"].tolist()
        paces = ed["Pace"].tolist()

        # Type 1: Shortest distance target (2% faster pace)
        min_pace_improved = paces[0] * 0.98
        rows.append((ex, distances[0], min_pace_improved))

        # Type 2: Gap fillers (between consecutive distances)
        for i in range(len(distances) - 1):
            if distances[i + 1] > distances[i] + 0.5:  # Gap of 0.5+ miles
                new_dist = distances[i] + 0.5
                # Estimate pace at new distance using Riegel's formula
                new_pace = estimate_pace_at_distance(paces[i], distances[i], new_dist)
                if not pd.isna(new_pace):
                    rows.append((ex, new_dist, new_pace))

        # Type 3: Longest distance target (variable increment)
        max_distance = distances[-1]
        if max_distance < 5:
            new_distance = max_distance + 0.5
        elif max_distance < 13:
            new_distance = max_distance + 1.0
        else:
            new_distance = max_distance * 1.10
        rows.append((ex, new_distance, paces[-1]))

    target_df = pd.DataFrame(rows, columns=["Exercise", "Distance", "Pace"])
    return add_speed_metric_column(target_df)


def predict_race_pace(
    df_records: pd.DataFrame, exercise: str, target_distance: float
) -> dict:
    """Predict target pace for a specific race distance.

    Uses Pareto front records to estimate achievable pace at target distance.
    Provides both optimistic (best case) and conservative (safe) estimates.

    Parameters
    ----------
    df_records : pd.DataFrame
        Pareto running records with columns: [Exercise, Distance, Pace]
    exercise : str
        Exercise name (e.g., "Running")
    target_distance : float
        Race distance in miles (e.g., 3.1 for 5K)

    Returns
    -------
    dict
        Dictionary with keys:
        - 'optimistic_pace': float (seconds/mile)
        - 'conservative_pace': float (seconds/mile)
        - 'optimistic_time': str (MM:SS total race time)
        - 'conservative_time': str (MM:SS total race time)

    Examples
    --------
    >>> predict_race_pace(df_records, "Running", 3.1)  # 5K prediction
    {
        'optimistic_pace': 540.0,
        'conservative_pace': 570.0,
        'optimistic_time': '27:54',
        'conservative_time': '29:27'
    }
    """

    ex_records = df_records[df_records["Exercise"] == exercise].sort_values("Distance")

    if ex_records.empty:
        return {
            "optimistic_pace": np.nan,
            "conservative_pace": np.nan,
            "optimistic_time": "N/A",
            "conservative_time": "N/A",
        }

    # Find closest Pareto points
    distances = ex_records["Distance"].values
    paces = ex_records["Pace"].values

    # Find nearest records (one shorter, one longer if available)
    shorter_idx = distances[distances <= target_distance]
    longer_idx = distances[distances >= target_distance]

    if len(shorter_idx) > 0:
        best_shorter = ex_records[ex_records["Distance"] == shorter_idx[-1]].iloc[0]
        optimistic = estimate_pace_at_distance(
            best_shorter["Pace"], best_shorter["Distance"], target_distance
        )
    else:
        # Extrapolate from shortest available
        optimistic = estimate_pace_at_distance(paces[0], distances[0], target_distance)

    if len(longer_idx) > 0:
        best_longer = ex_records[ex_records["Distance"] == longer_idx[0]].iloc[0]
        conservative = estimate_pace_at_distance(
            best_longer["Pace"], best_longer["Distance"], target_distance
        )
    else:
        # Use optimistic + 10% buffer
        conservative = optimistic * 1.10

    def total_time_str(pace_sec_per_mi: float, distance_mi: float) -> str:
        """Convert pace and distance to total time string."""
        if pd.isna(pace_sec_per_mi):
            return "N/A"
        total_seconds = pace_sec_per_mi * distance_mi
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    return {
        "optimistic_pace": optimistic,
        "conservative_pace": conservative,
        "optimistic_pace_str": seconds_to_pace_string(optimistic),
        "conservative_pace_str": seconds_to_pace_string(conservative),
        "optimistic_time": total_time_str(optimistic, target_distance),
        "conservative_time": total_time_str(conservative, target_distance),
    }
