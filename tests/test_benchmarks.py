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
    calculate_pareto_front,
    find_weakest_distance,
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

    np.random.seed(42)
    n = 500
    return pd.DataFrame(
        {
            "Distance (km)": np.random.uniform(1, 42.195, n),
            "Duration (min)": np.random.uniform(5, 300, n),
            "Date": pd.date_range("2020-01-01", periods=n, freq="D"),
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
    result = benchmark(calculate_pareto_front, df)
    assert len(result) > 0


def test_benchmark_find_weakest_distance(benchmark, large_running_dataset):
    """Benchmark finding weakest distance for running."""
    df = large_running_dataset.copy()
    pareto_df = calculate_pareto_front(df)
    result = benchmark(find_weakest_distance, pareto_df)
    assert result is not None
