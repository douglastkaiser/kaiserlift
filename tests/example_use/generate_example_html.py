import glob
from pathlib import Path

from kaiserlift import import_fitnotes_csv, gen_html_viewer


def main() -> None:
    """Generate an example HTML viewer from bundled sample data."""
    here = Path(__file__).parent
    csv_files = glob.glob(str(here / "FitNotes_Export_*.csv"))
    df = import_fitnotes_csv(csv_files)
    html = gen_html_viewer(df)
    out_dir = here / "build"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "example.html"
    out_file.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
