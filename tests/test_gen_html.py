from pathlib import Path
import inspect
import pytest
import kaiserlift

process_csv_files = getattr(kaiserlift, "process_csv_files", None)
if process_csv_files is None:
    pytest.skip("process_csv_files not available", allow_module_level=True)

gen_html_viewer = kaiserlift.gen_html_viewer


def test_gen_html_viewer_creates_html(tmp_path: Path) -> None:
    # Diagnostic to ensure we are testing the local source
    print("gen_html_viewer module path:", inspect.getfile(gen_html_viewer))
    csv_file = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df = process_csv_files([str(csv_file)])
    html = gen_html_viewer(df)
    out_file = tmp_path / "out.html"
    out_file.write_text(html, encoding="utf-8")
    assert out_file.exists()
    assert "<table" in html
    # ensure at least one exercise figure is present
    assert 'class="exercise-figure"' in html
    # upload controls should be present once and content wrapped in a single result div
    assert html.count('id="result"') == 1
    assert 'id="uploadButton"' in html
    assert 'id="csvFile"' in html
    assert 'id="uploadProgress"' in html


def test_gen_html_viewer_fragment_without_external_assets(tmp_path: Path) -> None:
    csv_file = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df = process_csv_files([str(csv_file)])
    html = gen_html_viewer(df, embed_assets=False)
    # Should not have external CDN scripts/styles
    assert "<script src=" not in html
    assert "<link href=" not in html
    # Should not have upload controls
    assert 'id="uploadButton"' not in html
    assert 'id="csvFile"' not in html
    assert 'id="result"' not in html
    assert 'id="uploadProgress"' not in html
    # Should not have full HTML page structure
    assert "<html>" not in html
    assert "<head>" not in html
    assert "<body>" not in html
    # Inline scripts for Plotly initialization are OK
    # (Interactive plots require JavaScript to function)


def test_gen_html_viewer_renders_non_ascii(tmp_path: Path) -> None:
    csv_file = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df = process_csv_files([str(csv_file)])
    df.loc[len(df)] = df.iloc[0]
    df.at[len(df) - 1, "Exercise"] = "Café del Mar"
    html = gen_html_viewer(df)
    out_file = tmp_path / "non_ascii.html"
    out_file.write_text(html, encoding="utf-8")
    contents = out_file.read_text(encoding="utf-8")
    assert '<meta charset="utf-8">' in html
    assert "Café del Mar" in contents
