import glob
import shutil
from pathlib import Path

from kaiserlift import gen_html_viewer, process_csv_files, gen_running_html_viewer, process_running_csv_files


def main() -> None:
    """Generate example HTML viewers from bundled sample data."""
    here = Path(__file__).parent
    out_dir = here / "build"
    out_dir.mkdir(exist_ok=True)

    # Generate lifting example
    csv_files = glob.glob(str(here / "FitNotes_Export_*.csv"))
    df = process_csv_files(csv_files)
    lifting_html = gen_html_viewer(df)
    for name in ("example.html", "index.html"):
        (out_dir / name).write_text(lifting_html, encoding="utf-8")

    # Generate running example
    running_csv = here / "running_sample.csv"
    if running_csv.exists():
        df_running = process_running_csv_files([running_csv])
        running_html = gen_running_html_viewer(df_running)
        (out_dir / "running.html").write_text(running_html, encoding="utf-8")

    # Copy client files
    client_dir = here.parent.parent / "client"
    for name in ("main.js", "version.js"):
        shutil.copy(client_dir / name, out_dir / name)


if __name__ == "__main__":
    main()
