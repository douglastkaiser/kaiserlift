#!/usr/bin/env python3
"""Pre-process CSV data files for optimal webpage loading performance.

This script implements three optimization strategies:

1. Filtered CSV: Creates lifting_filtered.csv with unnecessary data removed
   - Removes Cardio, Climbing, and specific exercises
   - Drops unused columns (Comment, Distance Unit, etc.)
   - Keeps human-readable CSV format for development

2. Pareto JSON: Pre-calculates Pareto-optimal data points
   - Computes highest_weight_per_rep() for each exercise
   - Outputs minimal JSON for maximum webpage performance
   - Includes 1RM calculations and next targets

3. Statistics JSON: Generates summary statistics
   - Per-exercise stats (record counts, date ranges, etc.)
   - Used for quick metadata display without loading full dataset

Usage:
    python scripts/preprocess_data.py

Output files:
    - data/lifting_filtered.csv
    - data/running_filtered.csv
    - data/pareto_data.json
    - data/stats.json
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from kaiserlift.df_processers import (
    process_csv_files,
    highest_weight_per_rep,
    add_1rm_column,
    df_next_pareto,
)


def preprocess_lifting_data(
    input_csv: Path, output_filtered_csv: Path, output_pareto_json: Path
) -> dict[str, Any]:
    """Pre-process lifting CSV data.

    Parameters
    ----------
    input_csv : Path
        Path to raw lifting CSV (e.g., data/lifting.csv)
    output_filtered_csv : Path
        Path for filtered CSV output (e.g., data/lifting_filtered.csv)
    output_pareto_json : Path
        Path for Pareto JSON output (e.g., data/pareto_data.json)

    Returns
    -------
    dict
        Statistics about the preprocessing (rows before/after, exercises, etc.)
    """
    print(f"📊 Processing lifting data from {input_csv}")

    # Load and process CSV using existing pipeline
    df_processed = process_csv_files([input_csv])

    # Calculate statistics BEFORE writing
    stats = {
        "total_rows": len(df_processed),
        "exercises": sorted(df_processed["Exercise"].unique().tolist()),
        "date_range": {
            "start": df_processed["Date"].min().isoformat(),
            "end": df_processed["Date"].max().isoformat(),
        },
        "categories": sorted(df_processed["Category"].unique().tolist()),
    }

    # Option 1: Write filtered CSV
    print(f"✅ Writing filtered CSV to {output_filtered_csv}")
    df_processed.to_csv(output_filtered_csv, index=False)
    print(
        f"   Reduced from original to {len(df_processed)} rows across {len(stats['exercises'])} exercises"
    )

    # Option 2: Calculate Pareto fronts and write JSON
    print("🎯 Calculating Pareto-optimal sets...")
    df_pareto = highest_weight_per_rep(df_processed)
    df_pareto_with_1rm = add_1rm_column(df_pareto)

    # Calculate next targets
    df_targets = df_next_pareto(df_pareto_with_1rm)

    # Convert to JSON-serializable format
    pareto_data = {
        "metadata": {
            "generated_from": str(input_csv),
            "total_workouts": len(df_processed),
            "pareto_sets": len(df_pareto_with_1rm),
            "date_range": stats["date_range"],
        },
        "exercises": {},
    }

    # Group by exercise for structured JSON
    for exercise in sorted(df_pareto_with_1rm["Exercise"].unique()):
        ex_pareto = df_pareto_with_1rm[df_pareto_with_1rm["Exercise"] == exercise]
        ex_targets = df_targets[df_targets["Exercise"] == exercise]

        pareto_data["exercises"][exercise] = {
            "pareto_front": ex_pareto[["Date", "Weight", "Reps", "1RM"]]
            .sort_values("Reps")
            .to_dict(orient="records"),
            "next_targets": ex_targets[["Weight", "Reps", "1RM"]]
            .sort_values("Reps")
            .to_dict(orient="records"),
            "record_count": len(ex_pareto),
        }

        # Convert Date objects to ISO strings
        for record in pareto_data["exercises"][exercise]["pareto_front"]:
            if "Date" in record and hasattr(record["Date"], "isoformat"):
                record["Date"] = record["Date"].isoformat()

    print(f"✅ Writing Pareto JSON to {output_pareto_json}")
    with output_pareto_json.open("w") as f:
        json.dump(pareto_data, f, indent=2)
    print(
        f"   Compressed {len(df_processed)} rows → {len(df_pareto_with_1rm)} Pareto-optimal sets"
    )

    return stats


def preprocess_running_data(
    input_csv: Path, output_filtered_csv: Path
) -> dict[str, Any]:
    """Pre-process running CSV data.

    Parameters
    ----------
    input_csv : Path
        Path to raw running CSV
    output_filtered_csv : Path
        Path for filtered CSV output

    Returns
    -------
    dict
        Statistics about the preprocessing
    """
    print(f"🏃 Processing running data from {input_csv}")

    # Read and basic processing (running data is already minimal)
    df = pd.read_csv(input_csv)
    df.columns = df.columns.str.strip()

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df = df.sort_values(by="Date", ascending=True)

    stats = {
        "total_rows": len(df),
        "date_range": {
            "start": df["Date"].min().isoformat(),
            "end": df["Date"].max().isoformat(),
        },
    }

    # Write filtered CSV
    print(f"✅ Writing filtered running CSV to {output_filtered_csv}")
    df.to_csv(output_filtered_csv, index=False)

    return stats


def main() -> None:
    """Main preprocessing pipeline."""
    print("=" * 60)
    print("🚀 KaiserLift Data Preprocessing Pipeline")
    print("=" * 60)

    # Setup paths
    repo_root = Path(__file__).parent.parent
    data_dir = repo_root / "data"

    input_lifting = data_dir / "lifting.csv"
    input_running = data_dir / "running.csv"

    output_lifting_filtered = data_dir / "lifting_filtered.csv"
    output_running_filtered = data_dir / "running_filtered.csv"
    output_pareto_json = data_dir / "pareto_data.json"
    output_stats_json = data_dir / "stats.json"

    all_stats = {}

    # Process lifting data
    if input_lifting.exists():
        lifting_stats = preprocess_lifting_data(
            input_lifting, output_lifting_filtered, output_pareto_json
        )
        all_stats["lifting"] = lifting_stats
    else:
        print(f"⚠️  Lifting CSV not found at {input_lifting}, skipping")

    # Process running data
    if input_running.exists():
        running_stats = preprocess_running_data(input_running, output_running_filtered)
        all_stats["running"] = running_stats
    else:
        print(f"⚠️  Running CSV not found at {input_running}, skipping")

    # Write combined statistics
    print(f"📈 Writing statistics to {output_stats_json}")
    with output_stats_json.open("w") as f:
        json.dump(all_stats, f, indent=2)

    print("\n" + "=" * 60)
    print("✨ Preprocessing complete!")
    print("=" * 60)
    print("\nGenerated files:")
    if output_lifting_filtered.exists():
        size_kb = output_lifting_filtered.stat().st_size / 1024
        print(f"  📄 {output_lifting_filtered} ({size_kb:.1f} KB)")
    if output_pareto_json.exists():
        size_kb = output_pareto_json.stat().st_size / 1024
        print(f"  📄 {output_pareto_json} ({size_kb:.1f} KB)")
    if output_running_filtered.exists():
        size_kb = output_running_filtered.stat().st_size / 1024
        print(f"  📄 {output_running_filtered} ({size_kb:.1f} KB)")
    if output_stats_json.exists():
        size_kb = output_stats_json.stat().st_size / 1024
        print(f"  📄 {output_stats_json} ({size_kb:.1f} KB)")
    print()


if __name__ == "__main__":
    main()
