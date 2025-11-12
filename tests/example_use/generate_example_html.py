import glob
import shutil
import subprocess
from pathlib import Path

from kaiserlift import (
    gen_html_viewer,
    process_csv_files,
    gen_running_html_viewer,
    process_running_csv_files,
)


def main() -> None:
    """Generate example HTML viewers from bundled sample data or personal data."""
    here = Path(__file__).parent
    repo_root = here.parent.parent
    data_dir = repo_root / "data"
    out_dir = here / "build"
    out_dir.mkdir(exist_ok=True)

    # Generate lifting example
    # Priority: use personal data from data/lifting.csv if available, else use example CSVs
    personal_lifting_csv = data_dir / "lifting.csv"
    if personal_lifting_csv.exists():
        print(f"Using personal lifting data from {personal_lifting_csv}")
        csv_files = [str(personal_lifting_csv)]
    else:
        print("Using example lifting data")
        csv_files = glob.glob(str(here / "FitNotes_Export_*.csv"))

    df = process_csv_files(csv_files)
    lifting_html = gen_html_viewer(df)
    (out_dir / "example.html").write_text(lifting_html, encoding="utf-8")

    # Generate running example with clean URL (running/index.html -> /running)
    # Priority: use personal data from data/running.csv if available, else use example CSV
    personal_running_csv = data_dir / "running.csv"
    if personal_running_csv.exists():
        print(f"Using personal running data from {personal_running_csv}")
        running_csv = personal_running_csv
    else:
        print("Using example running data")
        running_csv = here / "running_sample.csv"

    if running_csv.exists():
        df_running = process_running_csv_files([running_csv])
        running_html = gen_running_html_viewer(df_running)
        running_dir = out_dir / "running"
        running_dir.mkdir(exist_ok=True)
        (running_dir / "index.html").write_text(running_html, encoding="utf-8")

    # Generate landing page
    landing_script = here / "generate_landing_page.py"
    if landing_script.exists():
        subprocess.run(["python", str(landing_script)], check=True)

    # Copy client files
    client_dir = here.parent.parent / "client"
    for name in ("main.js", "version.js"):
        shutil.copy(client_dir / name, out_dir / name)


if __name__ == "__main__":
    main()
