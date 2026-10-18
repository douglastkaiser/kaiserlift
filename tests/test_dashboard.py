"""Regression coverage for the graph-first dashboard contract."""

import json
from html.parser import HTMLParser

import pandas as pd

from kaiserlift.viewers import gen_html_viewer
from kaiserlift.plot_utils import plotly_figure_to_html_div
import plotly.graph_objects as go


class DashboardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.panels = []
        self.payloads = []
        self.outputs = []
        self.in_payload = False
        self.in_output = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-exercise-panel" in attrs:
            self.panels.append(attrs)
        self.in_payload = tag == "script" and attrs.get("type") == "application/json"
        self.in_output = tag == "output"

    def handle_data(self, data):
        if self.in_payload:
            self.payloads.append(json.loads(data))
        if self.in_output:
            self.outputs.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_payload = False
        if tag == "output":
            self.in_output = False


def sample_lifts():
    return pd.DataFrame(
        {
            "Exercise": ["Squat", "Curl", "Curl"],
            "Category": ["Legs", "Arms", "Arms"],
            "Date": pd.to_datetime(["2025-01-01"] * 3),
            "Weight": [100.0, 40.0, 35.0],
            "Reps": [5, 5, 10],
        }
    )


def test_dashboard_shows_first_chart_and_matches_recommendation():
    html = gen_html_viewer(sample_lifts(), embed_assets=False)
    parser = DashboardParser()
    parser.feed(html)
    assert [panel["data-exercise-panel"] for panel in parser.panels] == [
        "Curl",
        "Squat",
    ]
    assert "hidden" not in parser.panels[0]
    assert "hidden" in parser.panels[1]
    assert html.index("data-exercise-panel") < html.index('id="exerciseTable"')
    for payload, output in zip(parser.payloads, parser.outputs, strict=True):
        recommendation = next(
            t for t in payload["data"] if t["name"] == "Recommended target"
        )
        assert (
            output
            == f"{recommendation['y'][0]:g} lbs × {recommendation['x'][0]:g} reps"
        )


def test_dashboard_escapes_exercise_names_in_controls_and_payloads():
    df = sample_lifts()
    df["Exercise"] = 'Curl "><script>alert(1)</script>'
    html = gen_html_viewer(df, embed_assets=False)
    parser = DashboardParser()
    parser.feed(html)
    assert parser.panels[0]["data-exercise-panel"] == df.iloc[0]["Exercise"]
    assert "<script>alert(1)</script>" not in html
    assert len(parser.payloads) == 1


def test_chart_payload_is_safe_to_restore_without_script_execution():
    fig = go.Figure(go.Scatter(x=[1], y=[2], name="</script><script>alert(1)</script>"))
    html = plotly_figure_to_html_div(fig, "test")
    parser = DashboardParser()
    parser.feed(html)
    assert len(parser.payloads) == 1
    assert parser.payloads[0]["data"][0]["name"] == fig.data[0].name
    assert "Plotly.newPlot" not in html
