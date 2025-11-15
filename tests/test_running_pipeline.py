"""Integration tests for running data pipeline."""

from pathlib import Path

from kaiserlift import running_pipeline


def test_running_pipeline_with_sample_data():
    """Test the full running pipeline with sample CSV data."""
    sample_file = Path(__file__).parent / "example_use" / "running_sample.csv"
    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    # Run the pipeline
    html_output = running_pipeline([sample_file])

    # Verify output is valid HTML
    assert isinstance(html_output, str)
    assert len(html_output) > 0
    assert "<html>" in html_output
    assert "<table" in html_output
    assert "Running" in html_output

    # Verify key components are present
    assert "runningTable" in html_output
    assert "plotly-graph-div" in html_output  # Plotly plot div
    assert "running-figure" in html_output  # Plot container div


def test_running_pipeline_fragment_mode():
    """Test pipeline in fragment mode (no embedded assets)."""
    sample_file = Path(__file__).parent / "example_use" / "running_sample.csv"

    html_fragment = running_pipeline([sample_file], embed_assets=False)

    # Should have table but no full HTML structure
    assert "<table" in html_fragment
    assert "<html>" not in html_fragment
    assert "<head>" not in html_fragment
