"""Simple FastAPI application for KaiserLift.

This module exposes two endpoints:

* ``GET /`` – serves an interactive page with a file input that posts to
  ``/upload`` using JavaScript.
* ``POST /upload`` – accepts the uploaded CSV, processes it with the core
  KaiserLift utilities and returns an HTML fragment rendered by
  :func:`render_viewer_fragment`.

The application can be started with ``python -m kaiserlift.webapp`` which will
launch a Uvicorn development server.
"""

from __future__ import annotations

import os
import pandas as pd

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

from . import df_next_pareto, gen_html_viewer, highest_weight_per_rep, process_csv_files
from .viewers import render_viewer_fragment


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Return the initial viewer page."""

    empty_df = pd.DataFrame(columns=["Exercise", "Reps", "Weight", "Category", "Date"])
    html = gen_html_viewer(empty_df)
    return HTMLResponse(
        f"<!DOCTYPE html><html><head><title>KaiserLift</title></head><body>{html}</body></html>"
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload(file: UploadFile = File(...)) -> HTMLResponse:
    """Process the uploaded CSV and return the viewer fragment."""

    df = process_csv_files([file.file])

    # These calls are executed separately to satisfy the requirement of running
    # each processing step explicitly.
    _records = highest_weight_per_rep(df)
    _targets = df_next_pareto(_records)

    html = render_viewer_fragment(df)
    return HTMLResponse(html)


def main() -> None:
    """Start a Uvicorn development server."""

    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("kaiserlift.webapp:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover - manual server start
    main()
