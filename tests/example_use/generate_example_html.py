import glob
import shutil
from pathlib import Path

from kaiserlift import gen_html_viewer, process_csv_files


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

    client_js = here.parent.parent / "client" / "main.js"
    shutil.copy(client_js, out_dir / "main.js")


if __name__ == "__main__":
    main()
