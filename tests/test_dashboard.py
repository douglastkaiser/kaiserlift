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
    assert len(parser.payloads) == len(parser.outputs)
    for payload, output in zip(parser.payloads, parser.outputs):
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


def test_home_and_labs_share_navigation_and_accessible_shell():
    from kaiserlift.site import render_home

    for html in (
        render_home(),
        render_home(server=True),
        gen_html_viewer(sample_lifts()),
    ):
        assert '<html lang="en">' in html
        assert 'aria-label="Main navigation"' in html
        assert 'class="skip-link"' in html
        assert 'id="main"' in html
        assert "fonts.googleapis.com" not in html
    assert 'action="/upload-running"' in render_home(server=True)
    assert 'href="running/#import"' in render_home()


def test_plot_theme_preserves_anchor_coordinates():
    from kaiserlift.viewers import plot_df

    records = sample_lifts()
    fig = plot_df(records, Exercise="Curl")
    original = [(list(trace.x), list(trace.y)) for trace in fig.data]
    parser = DashboardParser()
    parser.feed(plotly_figure_to_html_div(fig, "curl"))
    assert [
        (trace["x"], trace["y"]) for trace in parser.payloads[0]["data"]
    ] == original
    assert parser.payloads[0]["layout"]["plot_bgcolor"] == "#fffef8"


def test_plot_theme_keeps_pace_labels_in_minutes_and_seconds():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[420, 600]))
    fig.update_yaxes(
        type="log", tickmode="array", tickvals=[420, 600], ticktext=["7:00", "10:00"]
    )
    parser = DashboardParser()
    parser.feed(plotly_figure_to_html_div(fig, "pace"))
    assert parser.payloads[0]["layout"]["yaxis"]["ticktext"] == ["7:00", "10:00"]
