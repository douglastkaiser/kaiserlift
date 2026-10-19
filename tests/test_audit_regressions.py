"""Regression coverage for package contracts discovered during the audit."""

import importlib
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

import kaiserlift
from kaiserlift.df_processers import highest_1rm_per_rep, highest_weight_per_rep
from kaiserlift.running_processers import (
    highest_pace_per_distance,
    highest_pace_per_distance_pace_pareto,
    predict_race_pace,
    process_running_csv_files,
)


@pytest.mark.parametrize("function", [highest_weight_per_rep, highest_1rm_per_rep])
def test_lifting_pareto_ignores_duplicate_index_labels(function):
    df = pd.DataFrame(
        {"Exercise": ["Curl"] * 3, "Weight": [100, 90, 80], "Reps": [5, 10, 5]}
    )
    expected = function(df).reset_index(drop=True)
    df.index = [0, 0, 0]
    original = df.copy(deep=True)
    pd.testing.assert_frame_equal(function(df).reset_index(drop=True), expected)
    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize(
    "function", [highest_pace_per_distance, highest_pace_per_distance_pace_pareto]
)
def test_running_pareto_ignores_duplicate_index_labels(function):
    df = pd.DataFrame(
        {"Exercise": ["Running"] * 3, "Distance": [3, 5, 3], "Pace": [540, 570, 600]}
    )
    expected = function(df).reset_index(drop=True)
    df.index = [0, 0, 0]
    original = df.copy(deep=True)
    pd.testing.assert_frame_equal(function(df).reset_index(drop=True), expected)
    pd.testing.assert_frame_equal(df, original)


def test_running_csv_accepts_explicit_pace():
    csv = io.StringIO(
        "Date,Exercise,Category,Distance,Pace\n2025-01-01,Running,Cardio,3,540\n"
    )
    df = process_running_csv_files([csv])
    assert df["Pace"].tolist() == [540]


def test_running_csv_preserves_pace_and_fills_missing_from_duration():
    csv = io.StringIO(
        "Date,Exercise,Category,Distance,Pace,Duration\n"
        "2025-01-01,Running,Cardio,3,500,27\n"
        "2025-01-02,Running,Cardio,3,,27\n"
    )
    assert process_running_csv_files([csv])["Pace"].tolist() == [500, 540]


def test_race_prediction_bounds_remain_ordered_with_uneven_history():
    df = pd.DataFrame(
        {"Exercise": ["Running"] * 2, "Distance": [3, 10], "Pace": [600, 500]}
    )
    prediction = predict_race_pace(df, "Running", 5)
    assert prediction["optimistic_pace"] <= prediction["conservative_pace"]
    assert prediction["optimistic_time"] == "39:58"
    assert prediction["conservative_time"] == "51:33"


@pytest.mark.parametrize(
    ("module_name", "entrypoint", "processor", "viewer"),
    [
        ("pipeline", "pipeline", "process_csv_files", "gen_html_viewer"),
        (
            "running_pipeline",
            "running_pipeline",
            "process_running_csv_files",
            "gen_running_html_viewer",
        ),
    ],
)
def test_csv_pipeline_only_loads_and_delegates(
    module_name, entrypoint, processor, viewer
):
    module = importlib.import_module(f"kaiserlift.{module_name}")
    df = pd.DataFrame({"Exercise": ["Example"]})
    files = [io.StringIO("csv")]
    with patch.object(module, processor, return_value=df) as load:
        with patch.object(module, viewer, return_value="html") as render:
            assert getattr(module, entrypoint)(files, embed_assets=False) == "html"
    load.assert_called_once_with(files)
    render.assert_called_once_with(df, embed_assets=False)


def test_package_contains_server_assets():
    assets = Path(kaiserlift.__file__).parent / "assets"
    for filename in ("main.js", "lifting_sample.csv", "running_sample.csv"):
        assert (assets / filename).is_file()


def test_cli_help_works_without_starting_server(capsys):
    from kaiserlift.main import main

    with patch("sys.argv", ["kaiserlift-cli", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
    assert "web interface" in capsys.readouterr().out


def test_installed_cli_outside_checkout(tmp_path):
    cli = Path(sys.executable).with_name("kaiserlift-cli")
    result = subprocess.run(
        [str(cli), "--help"], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert "web interface" in result.stdout


def test_cli_reports_missing_server_dependency(capsys):
    from kaiserlift.main import main

    error = ModuleNotFoundError("No module named 'uvicorn'", name="uvicorn")
    with patch("sys.argv", ["kaiserlift-cli"]):
        with patch.dict(
            sys.modules, {"kaiserlift.webapp": Mock(main=Mock(side_effect=error))}
        ):
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == 2
    assert 'pip install "kaiserlift[server]"' in capsys.readouterr().err
