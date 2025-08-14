from pathlib import Path
import inspect
import pytest
import kaiserlift

process_csv_files = getattr(kaiserlift, "process_csv_files", None)
if process_csv_files is None:
    pytest.skip("process_csv_files not available", allow_module_level=True)

gen_html_viewer = kaiserlift.gen_html_viewer

CSV_FILE = (
    Path(__file__).parent / "example_use" / "FitNotes_Export_2025_05_21_08_39_11.csv"
)


def test_gen_html_viewer_creates_html(tmp_path: Path) -> None:
    # Diagnostic to ensure we are testing the local source
    print("gen_html_viewer module path:", inspect.getfile(gen_html_viewer))
    df = process_csv_files([str(CSV_FILE)])
    html = gen_html_viewer(df)
    out_file = tmp_path / "out.html"
    out_file.write_text(html, encoding="utf-8")
    assert out_file.exists()
    assert "<table" in html
    # ensure at least one exercise figure is present
    assert 'class="exercise-figure"' in html


def test_gen_html_viewer_no_script_tags() -> None:
    if "embed_assets" not in inspect.signature(gen_html_viewer).parameters:
        pytest.skip("embed_assets parameter not supported")
    df = process_csv_files([str(CSV_FILE)])
    html = gen_html_viewer(df, embed_assets=False)
    assert "<script" not in html.lower()
