"""Performance benchmarks for kaiserlift key operations."""

import pandas as pd
import pytest
from kaiserlift import (
    calculate_1rm,
    add_1rm_column,
    df_next_pareto,
    highest_weight_per_rep,
)
from kaiserlift.running_processers import (
    highest_pace_per_distance,
    df_next_running_targets,
)


@pytest.fixture
def large_lifting_dataset():
    """Generate a large dataset for lifting benchmarks."""
    import numpy as np

    np.random.seed(42)
    n = 1000
    return pd.DataFrame(
        {
            "Exercise": ["Bench Press"] * n,
            "Weight": np.random.randint(100, 300, n),
            "Reps": np.random.randint(1, 15, n),
            "Date": pd.date_range("2020-01-01", periods=n, freq="D"),
        }
    )


@pytest.fixture
def large_running_dataset():
    """Generate a large dataset for running benchmarks."""
    import numpy as np
    from datetime import datetime

    np.random.seed(42)
    n = 500
    return pd.DataFrame(
        {
            "Date": [datetime(2020, 1, 1)] * n,
            "Exercise": ["Running"] * n,
            "Category": ["Cardio"] * n,
            "Distance": np.random.uniform(1, 26.2, n),  # Up to marathon distance
            "Pace": np.random.uniform(360, 720, n),  # 6:00 to 12:00 min/mile in seconds
        }
    )


def test_benchmark_calculate_1rm(benchmark):
    """Benchmark 1RM calculation."""
    result = benchmark(calculate_1rm, 225, 8)
    assert result > 0


def test_benchmark_add_1rm_column(benchmark, large_lifting_dataset):
    """Benchmark adding 1RM column to large dataset."""
    df = large_lifting_dataset.copy()
    result = benchmark(add_1rm_column, df)
    assert "1RM" in result.columns
    assert len(result) == len(df)


def test_benchmark_highest_weight_per_rep(benchmark, large_lifting_dataset):
    """Benchmark finding highest weight per rep."""
    df = large_lifting_dataset.copy()
    result = benchmark(highest_weight_per_rep, df)
    assert len(result) > 0


def test_benchmark_df_next_pareto(benchmark, large_lifting_dataset):
    """Benchmark Pareto front calculation for lifting."""
    df = add_1rm_column(large_lifting_dataset.copy())
    result = benchmark(df_next_pareto, df)
    assert len(result) > 0


def test_benchmark_running_pareto_front(benchmark, large_running_dataset):
    """Benchmark Pareto front calculation for running."""
    df = large_running_dataset.copy()
    result = benchmark(highest_pace_per_distance, df)
    assert len(result) > 0


def test_benchmark_running_targets(benchmark, large_running_dataset):
    """Benchmark generating running targets."""
    df = large_running_dataset.copy()
    pareto_df = highest_pace_per_distance(df)
    result = benchmark(df_next_running_targets, pareto_df)
    assert len(result) > 0
