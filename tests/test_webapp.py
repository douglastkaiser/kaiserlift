"""Tests for the FastAPI web application."""

from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    from kaiserlift.webapp import app
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pytest.skip(
        "fastapi and kaiserlift.webapp are required for these tests",
        allow_module_level=True,
    )

client = TestClient(app)


def test_get_root() -> None:
    """The index route should return an HTML form."""

    response = client.get("/")
    assert response.status_code == 200
    assert "<form" in response.text


def test_upload_csv() -> None:
    """Uploading a CSV should return generated HTML."""

    csv_path = Path("tests/example_use/FitNotes_Export_2025_05_21_08_39_11.csv")
    with csv_path.open("rb") as fh:
        response = client.post(
            "/upload", files={"file": (csv_path.name, fh, "text/csv")}
        )

    assert response.status_code == 200
    assert "exercise-figure" in response.text
    # ``upload`` should return a standalone HTML page with embedded assets.
    assert "<!DOCTYPE html>" in response.text
    assert "<script" in response.text
    assert response.text.count('id="result"') == 1
