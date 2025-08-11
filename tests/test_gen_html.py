from pathlib import Path

from kaiserlift import gen_html_viewer, import_fitnotes_csv


def test_gen_html_viewer_creates_html(tmp_path: Path) -> None:
    csv_file = (
        Path(__file__).parent
        / "example_use"
        / "FitNotes_Export_2025_05_21_08_39_11.csv"
    )
    df = import_fitnotes_csv([str(csv_file)])
    html = gen_html_viewer(df)
    out_file = tmp_path / "out.html"
    out_file.write_text(html, encoding="utf-8")
    assert out_file.exists()
    assert "<table" in html
    assert 'data-fig="Flat_Barbell_Bench_Press"' in html
    assert 'id="fig-Flat_Barbell_Bench_Press"' in html
