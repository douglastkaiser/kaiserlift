import pandas as pd
import matplotlib

matplotlib.use("Agg")

from kaiserlift.viewers import gen_html_viewer, _sanitize_for_id


def test_gen_html_viewer_sanitizes_ids():
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "Exercise": ["Dumbbell Curl", "Barbell Squat"],
            "Category": ["Biceps", "Legs"],
            "Weight": [30, 100],
            "Reps": [10, 5],
        }
    )

    html = gen_html_viewer(df)

    for ex in df["Exercise"].unique():
        sanitized = _sanitize_for_id(ex)
        assert f'id="fig-{sanitized}"' in html
