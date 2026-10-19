"""Command-line entry point with an optional web server dependency."""

import argparse


def main() -> None:
    """Start the web interface, or explain how to install its dependencies."""
    parser = argparse.ArgumentParser(description="Start the KaiserLift web interface.")
    parser.parse_args()
    try:
        from .webapp import main as serve

        serve()
    except ModuleNotFoundError as exc:
        if exc.name not in {"fastapi", "uvicorn", "multipart", "python_multipart"}:
            raise
        parser.error('Install the web interface with: pip install "kaiserlift[server]"')
