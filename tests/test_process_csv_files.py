from pathlib import Path
import pytest
import kaiserlift

process_csv_files = getattr(kaiserlift, "process_csv_files", None)
if process_csv_files is None:
    pytest.skip("process_csv_files not available", allow_module_level=True)

import_fitnotes_csv = kaiserlift.import_fitnotes_csv
assert_frame_equal = kaiserlift.assert_frame_equal


def test_process_csv_files_path_vs_fileobj():
    csv_path = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df_from_path = process_csv_files([csv_path])
    with csv_path.open("r", encoding="utf-8") as f:
        df_from_obj = process_csv_files([f])
    assert_frame_equal(df_from_path, df_from_obj)


def test_import_fitnotes_csv_wrapper():
    csv_path = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df_new = process_csv_files([csv_path])
    df_old = import_fitnotes_csv([csv_path])
    assert_frame_equal(df_new, df_old)


def test_process_csv_files_weight_lbs_column(tmp_path):
    csv_content = "\n".join(
        [
            "Date,Exercise,Category,Weight (lbs),Weight Unit,Reps,Distance,Distance Unit,Time,Comment",
            "2024-01-01,Bench Press,Chest,100,lbs,5,,,,",
        ]
    )
    csv_path = tmp_path / "weight_lbs.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    df = process_csv_files([csv_path])
    assert "Weight" in df.columns
    assert df.loc[0, "Weight"] == 100
    assert df.loc[0, "Reps"] == 5


def test_process_csv_files_weight_column_with_whitespace(tmp_path):
    csv_content = "\n".join(
        [
            "Date,Exercise,Category, Weight (lbs),Weight Unit,Reps,Distance,Distance Unit,Time,Comment",
            "2024-01-01,Bench Press,Chest,100,lbs,5,,,,",
        ]
    )
    csv_path = tmp_path / "weight_lbs_spaced.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    df = process_csv_files([csv_path])
    assert "Weight" in df.columns
    assert df.loc[0, "Weight"] == 100
