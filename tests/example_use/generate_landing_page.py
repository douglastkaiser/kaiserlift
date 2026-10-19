"""Generate the same neo-retro landing page as the FastAPI application."""

from pathlib import Path

from kaiserlift.site import render_home


def main() -> None:
    """Write the static home page next to the generated lab directories."""
    out_dir = Path(__file__).parent / "build"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(render_home(), encoding="utf-8")


if __name__ == "__main__":
    main()
