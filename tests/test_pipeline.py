from pathlib import Path

import kaiserlift


pipeline = getattr(kaiserlift, "pipeline")


def test_pipeline_generates_html() -> None:
    csv_path = Path("tests/example_use/FitNotes_Export_2025_05_21_08_39_11.csv")
    with csv_path.open("rb") as fh:
        html = pipeline([fh])
    assert "<table" in html
