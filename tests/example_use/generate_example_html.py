import glob
from pathlib import Path

from kaiserlift import process_csv_files, gen_html_viewer


def main() -> None:
    """Generate an example HTML viewer from bundled sample data."""
    here = Path(__file__).parent
    csv_files = glob.glob(str(here / "FitNotes_Export_*.csv"))
    df = process_csv_files(csv_files)
    html = gen_html_viewer(df)
    out_dir = here / "build"
    out_dir.mkdir(exist_ok=True)
    for name in ("example.html", "index.html"):
        (out_dir / name).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
