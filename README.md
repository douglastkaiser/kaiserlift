# 🏋️ KaiserLift

[![PyPI version](https://badge.fury.io/py/kaiserlift.svg)](https://pypi.org/project/kaiserlift/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A smarter way to choose your next workout: data-driven progressive overload**

🎯 **Never guess your next workout again** — KaiserLift analyzes your training history and tells you exactly which exercise, weight, and rep range will give you the easiest PR.

## ✨ Quick Start

### Installation

```bash
pip install kaiserlift
```

Or with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv pip install kaiserlift
```

### Run the Web Interface

```bash
kaiserlift-cli
```

Then open http://localhost:8000 in your browser and upload your FitNotes CSV export.

### Use as a Python Library

```python
from kaiserlift import pipeline

# Generate interactive HTML with workout recommendations
html = pipeline(["your_fitnotes_export.csv"])
with open("workout_plan.html", "w") as f:
    f.write(html)
```

### CSV Data Format

Your CSV should follow the FitNotes export format:

```csv
Date,Exercise,Category,Weight,Reps
2022-09-14,Flat Barbell Bench Press,Chest,45.0,10
2022-09-14,Dumbbell Curl,Biceps,35.0,10
```

## Why keep doing 10 rep sets? Are you pushing in a smart way?

The core idea I’m exploring is simple: I want a science-based system for determining what’s the best workout to do next if your goal is muscle growth. The foundation of this is progressive overload—the principle that muscles grow when you consistently challenge them beyond what they’re used to.

One of the most effective ways to apply progressive overload is by taking sets to failure. But doing that intelligently requires knowing what you’ve done before. If you have a record of your best sets on a given exercise, you can deliberately aim to push past those PRs. That history becomes your benchmark.

![Rawdata Curl Pulldown](images/RawDataCurlPulldownBicep.png "Rawdata Curl Pulldown")

Now, there’s another dimension to this: rep range adaptation. If you always train for, say, 10 reps, your muscles can get used to that rep range—even if you’re still pushing for PRs. Switching things up and going for, say, 20-rep maxes (even with lighter weight) can stimulate growth by forcing the muscle to adapt to new challenges. Then, when you go back to 10 reps, you might find you’ve blown through a plateau.

To make this system more precise, I propose using a one-rep max (1RM) equivalence formula—a way of mapping rep and weight combinations onto a single curve. It gives you a way to compare different PRs across rep ranges. Using that, you can identify which rep range you’re weakest in—meaning, which PR has the lowest 1RM equivalent. That’s where your next opportunity lies.

![Curl Pulldown with Pareto](images/CurlPulldownwithPareto.png "Curl Pulldown with Pareto")

For the 1 rep max we use [`The Epley Formula`](https://en.wikipedia.org/wiki/One-repetition_maximum#cite_ref-7):
$$
\text{estimated\_1rm} = \text{weight} \times \left(1 + \frac{\text{reps}}{30.0}\right)
$$

## Here's how to operationalize it:

1. Collect your full workout history for a given exercise—every weight and rep combo you’ve done.
2. Calculate the Pareto front of that data. This is the set of “non-dominated” performances: the heaviest weights at each rep range that can’t be beaten in both weight and reps at the same time.
3. For each point on the Pareto front, compute the 1RM equivalent using a decay-style formula.
4. Identify the Pareto front point with the lowest 1RM equivalent—that’s your weakest spot.
5. Now, generate a “next step” PR target: a new set that just barely beats that weakest point, by the smallest reasonable margin (e.g., +1 rep or +5 lbs). That becomes your next workout goal.

This method gives you a structured, data-driven way to chase the easiest possible PR—which is still a PR. That keeps you progressing without burning out.

You can extend this concept across exercises too. Let’s say it’s biceps day. Instead of defaulting to the same curl variation you always do, you can rotate in a bicep exercise you haven’t done recently in order to assure a new PR. This introduces variability, which is another powerful way to drive adaptation while still targeting the same muscle group.

![Curl Pulldown with Targets](images/CurlPulldownwithTargets.png "Curl Pulldown with Targets")

The end goal here is simple: use your data to intelligently apply progressive overload, break through plateaus, and train more effectively—with zero guesswork.

To this end I also made an HTML page that can organize these in a text searchable way and can be accessed from my phone at the gym. This table of taget sets can be ordered by 1RPM and so easilly parsed.

![Curl Pulldown Example - HTML](images/curlpulldown_html.png "Curl Pulldown Example - HTML")

## Advanced Usage

### Development

Set up a local environment with [uv](https://docs.astral.sh/uv/):

```
uv venv
uv sync
```

Import data and run the pareto calculations:
```
from kaiserlift import (
    process_csv_files,
    highest_weight_per_rep,
    df_next_pareto,
)
csv_files = glob.glob("*.csv")
df = process_csv_files(csv_files)
df_pareto = highest_weight_per_rep(df)
df_targets = df_next_pareto(df_pareto)
```

Plotting the data:
```
from kaiserlift import plot_df

# Simple view of all data (only the blue dots)
fig = plot_df(df, Exercise="Dumbbell Curl")
fig.savefig("build/Dumbbell_Curl_Raw.png")

# View with pareto front plotted (the red line)
fig = plot_df(df, df_pareto=df_pareto, Exercise="Dumbbell Curl")
fig.savefig("build/Dumbbell_Curl_Pareto.png")

# View with pareto and targets (the green x's)
fig = plot_df(df, df_pareto=df_pareto, df_targets=df_targets, Exercise="Dumbbell Curl")
fig.savefig("build/Dumbbell_Curl_Pareto_and_Targets.png")
```

Generate views:
```
from kaiserlift import (
    print_oldest_exercise,
    gen_html_viewer,
)

# Console print out with optional args
output_lines = print_oldest_exercise(df, n_cat=2, n_exercises_per_cat=2, n_target_sets_per_exercises=2)
with open("your_workout_summary.txt", "w") as f:
    f.writelines(output_lines)

# Print in HTML format for ease of use
full_html = gen_html_viewer(df)
with open("your_interactive_table.html", "w", encoding="utf-8") as f:
    f.write(full_html)

# Console print of the HTML
from IPython.display import display, HTML
display(HTML(full_html))
```

### Example HTML generation in CI

An example dataset and helper script live in `tests/example_use`. You can
generate the interactive HTML table locally with:

```
python tests/example_use/generate_example_html.py
```

The "Generate example HTML" job in the CI workflow runs the same script. If
GitHub Pages is enabled for the repository, the resulting `example.html`
(also copied to `index.html` so the root URL renders the page) is deployed to
a temporary Pages site and linked in the job summary for quick preview.
Otherwise, the HTML remains available as a downloadable artifact.
