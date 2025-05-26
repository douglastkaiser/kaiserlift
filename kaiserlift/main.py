import pandas as pd
import numpy as np
import os
import glob
import math
import matplotlib.pyplot as plt

# Get a list of all CSV files in the current directory
working_dir = '/content/drive/MyDrive/Personal Work/Workout Analysis (90%)/'
csv_files = glob.glob(working_dir+'FitNotes_Export_*.csv')

# Find the file with the most recent timestamp
latest_file = max(csv_files, key=os.path.getctime)
print(f"Using {latest_file}")

# Load the latest file into a pandas DataFrame
df = pd.read_csv(latest_file)

def assert_frame_equal(df1, df2):
    assert df1.shape == df2.shape, "DataFrames have different shapes." + \
      f"\n{df1=}\n{df2=}"
    assert sorted(df1.columns) == sorted(df2.columns), "DataFrames have different column names." + \
      f"\n{df1=}\n{df2=}"
    # Ensure column order is the same before sorting rows
    df1_reordered_cols = df1.sort_index(axis=1)
    df2_reordered_cols = df2.sort_index(axis=1)
    # Reset index, sort by all columns, reset index again
    df1_processed = df1_reordered_cols.reset_index(drop=True)\
                                      .sort_values(by=df1_reordered_cols.columns.tolist())\
                                      .reset_index(drop=True)
    df2_processed = df2_reordered_cols.reset_index(drop=True)\
                                      .sort_values(by=df2_reordered_cols.columns.tolist())\
                                      .reset_index(drop=True)
    assert df1_processed.equals(df2_processed), f'\n{df1_processed}\nnot equal to\n{df2_processed}'

assert_frame_equal(
    pd.DataFrame({'Weight':[100], 'Reps':[1]}),
    pd.DataFrame({'Weight':[100], 'Reps':[1]})
)

try:
  assert_frame_equal(
      pd.DataFrame({'Weight':[100], 'Reps':[1]}),
      pd.DataFrame({'Weight':[100], 'Reps':[2]})
  )
except AssertionError as e:
  assert "not equal to" in f"{e}"


def highest_weight_per_rep(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure required columns exist
    required_cols = ['Exercise', 'Weight', 'Reps']
    assert all(col in df.columns for col in required_cols)

    # --- Make it simple: Basic Checks and Copy ---
    # Work on a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Convert Weight and Reps to numeric, coercing errors to NaN
    df_copy['Weight'] = pd.to_numeric(df_copy['Weight'], errors='coerce')
    df_copy['Reps'] = pd.to_numeric(df_copy['Reps'], errors='coerce')

    # Drop rows where Weight or Reps are invalid/missing for this calculation
    df_copy = df_copy.dropna(subset=['Exercise', 'Weight', 'Reps'])

    # Ensure Reps are integers if possible (or handle floats if necessary)
    df_copy['Reps'] = df_copy['Reps'].astype(int)

    if df_copy.empty:
         # Return an empty DataFrame with the original columns structure
         return pd.DataFrame(columns=df.columns)


    # --- Core Logic ---

    # Step 1: Find the row index corresponding to the max weight for each (Exercise, Reps) pair.
    # This handles cases where the same max weight/rep was achieved multiple times,
    # picking one instance (the first one encountered in the original df order by default).
    # Using idxmax ensures we keep the entire row data associated with that max weight.
    idx = df_copy.groupby(['Exercise', 'Reps'])['Weight'].idxmax()
    max_weight_sets = df_copy.loc[idx].copy() # Create df of potential PRs

    # Step 2: Filter based on the superseding rule.
    # A record (W, R) is superseded if there exists another record (W', R') for the same exercise
    # such that R' > R and W' >= W.

    # Define a function to check if a row is superseded within its group
    def is_superseded(row, group_df):
        # Check for rows in the same exercise group
        # with strictly more reps AND greater than or equal weight
        superseding_rows = group_df[
            (group_df['Reps'] > row['Reps']) &
            (group_df['Weight'] >= row['Weight'])
        ]
        # Return True if any such row exists (meaning the current row IS superseded)
        return not superseding_rows.empty

    # Apply this check group-wise
    final_record_indices = []
    # Group the potential PRs by exercise
    for exercise_name, group in max_weight_sets.groupby('Exercise'):
        # Apply the check function to each row (axis=1) within the group
        # We want rows where is_superseded is False
        rows_to_keep = group[~group.apply(lambda row: is_superseded(row, group), axis=1)]
        final_record_indices.extend(rows_to_keep.index.tolist())

    # Filter the max_weight_sets DataFrame using the collected indices
    final_df = max_weight_sets.loc[final_record_indices]

    return final_df

# Should be the same for 100x1 only.
assert_frame_equal(
  highest_weight_per_rep(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100],
    'Reps':[1],
  })),
  pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100],
    'Reps':[1],
  })
)

# Fake out, 90x5 should be dropped in favor of 100x10
assert_frame_equal(
  highest_weight_per_rep(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100, 90],
    'Reps':[10, 5],
  })),
  pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100],
    'Reps':[10],
  })
)

# Real now, 90x15, 110x1, and 100x10 will be kept, all others dropped.
assert_frame_equal(
  highest_weight_per_rep(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100, 90, 100, 95, 110],
    'Reps':  [10,  15,   5,  3,  1],
  })),
  pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100, 90, 110],
    'Reps':[10, 15, 1],
  })
)

def calculate_1rm(weight: float, reps: int) -> float:
    # Input validation
    if weight is None or reps is None or \
       math.isnan(weight) or math.isnan(reps) or \
       (reps <= 0) or (weight <= 0):
           # Allow weight == 0 (e.g. bodyweight exercises recorded as 0)
           # but 1RM is meaningless if weight is negative or reps <= 0
        if (weight == 0) and (reps > 0):
            return 0.0 # 1RM for 0 weight is 0
        return np.nan # Invalid input for calculation

    # If reps is 1, the 1RM is simply the weight lifted.
    if reps == 1:
        return float(weight)

    # Apply the Epley formula
    estimated_1rm = weight * (1 + reps / 30.0)

    return estimated_1rm

assert calculate_1rm(100, 1) == 100.0
assert calculate_1rm(1, 15) == 1.5

def estimate_weight_from_1rm(one_rm: float, reps: int) -> float:
    # Input validation
    if one_rm is None or reps is None or \
       math.isnan(one_rm) or math.isnan(reps) or \
       (reps <= 0) or (one_rm < 0):
        if (one_rm == 0) and (reps > 0):
            return 0.0
        return np.nan

    if reps == 1:
        return float(one_rm)

    estimated_weight = one_rm / (1 + reps / 30.0)

    return estimated_weight

assert estimate_weight_from_1rm(200, 1) == 200.0
assert estimate_weight_from_1rm(200, 4) == 176.47058823529412
assert calculate_1rm(estimate_weight_from_1rm(200, 4), 4) == 200.0


def add_1rm_column(df: pd.DataFrame) -> pd.DataFrame:
    # Check if necessary columns exist
    required_cols = ['Weight', 'Reps']
    assert all(col in df.columns for col in required_cols), \
      f"Warning: DataFrame must contain columns: {required_cols} to calculate 1RM. Returning original DataFrame."

    # Work on a copy to avoid modifying the original DataFrame
    df_copy = df.copy()

    # Ensure 'Weight' and 'Reps' are numeric, coercing errors to NaN
    # This prepares the columns for the calculation function
    df_copy['Weight'] = pd.to_numeric(df_copy['Weight'], errors='coerce')
    df_copy['Reps'] = pd.to_numeric(df_copy['Reps'], errors='coerce')

    # Apply the calculate_1rm function row-wise
    # It iterates through rows and passes 'Weight' and 'Reps' to calculate_1rm
    # The result of apply is a Series which becomes the new '1RM' column
    df_copy['1RM'] = df_copy.apply(
        lambda row: calculate_1rm(row['Weight'], row['Reps']),
        axis=1 # Apply function row-wise
    )

    # Optional: Round the 1RM column for cleaner presentation
    # df_copy['1RM'] = df_copy['1RM'].round(2)

    return df_copy

# Should be the same for 100x1 only.
assert_frame_equal(
  add_1rm_column(pd.DataFrame({
    'Weight':[100],
    'Reps':[1],
  })),
  pd.DataFrame({
    'Weight':[100],
    'Reps':[1],
    '1RM':[100.0],
  })
)

# More real values. w*(1+r/30.0)
assert_frame_equal(
  add_1rm_column(pd.DataFrame({
    'Weight':[100, 1, 13],
    'Reps':[30, 15, 1],
  })),
  pd.DataFrame({
    'Weight':[100, 1, 13],
    'Reps':[30, 15, 1],
    '1RM':[200.0, 1.5, 13.0],
  })
)


def dougs_next_pareto(df_records):
    rows = []
    for ex in df_records['Exercise'].unique():
        ed = df_records[df_records['Exercise']==ex].sort_values('Reps')
        ws = ed['Weight'].tolist()
        rs = ed['Reps'].tolist()

        # first‐rep side
        rows.append((ex, ws[0]+5, 1))

        # gaps in the middle
        for i in range(len(rs)-1):
            if rs[i+1] > rs[i] + 1:
                nr = rs[i] + 1
                # two candidates: step rep on low, or step weight on high
                c1_w = ws[i]
                c2_w = ws[i+1] + 5
                rows.append((ex, min(c1_w, c2_w), nr))

        # high‐rep end
        rows.append((ex, ws[-1], rs[-1]+1))

    return add_1rm_column(pd.DataFrame(rows, columns=['Exercise','Weight','Reps']))


# Simple case for 100x1; 105x1 and 100x2
assert_frame_equal(
  dougs_next_pareto(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100],
    'Reps':[1],
  })),
  add_1rm_column(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[105, 100],
    'Reps':[1, 2],
  }))
)

assert_frame_equal(
  dougs_next_pareto(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100],
    'Reps':[5],
  })),
  add_1rm_column(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[105, 100],
    'Reps':[1, 6],
  }))
)

# Two excersice test
assert_frame_equal(
  dougs_next_pareto(pd.DataFrame({
    'Exercise':['Bench Press'] + ['Incline Bench Press']*2,
    'Weight':[100] + [80, 50],
    'Reps':[5] + [1, 10],
  })),
  add_1rm_column(pd.DataFrame({
    'Exercise':['Bench Press']*2 + ['Incline Bench Press']*3,
    'Weight':[105, 100] + [85, 55, 50],
    'Reps':[1, 6] + [1, 2, 11],
  }))
)

# Okay the big case now. Lowest next set on the pareto front.
# First entry not on rep 1
# Gaps in both rep and weight
# Single increment off example (80x5 and 75x6)
assert_frame_equal(
  dougs_next_pareto(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[100, 80, 75, 50],
    'Reps':[2, 5, 6, 10],
  })),
  add_1rm_column(pd.DataFrame({
    'Exercise':'Bench Press',
    'Weight':[105, 85, 55, 50],
    'Reps':  [  1,  3, 7, 11],
  }))
)

from difflib import get_close_matches
def get_closest_exercise(df, Exercise):
    all_exercises = df['Exercise'].unique()
    matches = get_close_matches(Exercise, all_exercises, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    else:
        raise ValueError(f"No close match found for '{Exercise}'.")

def plot_df(df, df_pareto=None, df_targets=None, Exercise: str = None):
    df = df[df['Reps'] != 0]

    if Exercise is None:
        exercises = df['Exercise'].unique()
        fig, ax = plt.subplots()
        for exercise in exercises:
            exercise_df = df[df['Exercise'] == exercise]
            ax.scatter(exercise_df['Reps']/max(exercise_df['Reps']), exercise_df['Weight']/max(exercise_df['Weight']), label=exercise)
        ax.set_title("Weight vs. Reps for All Exercises")
        ax.set_xlabel("Reps")
        ax.set_ylabel("Weight")
        return fig

    closest_match = get_closest_exercise(df, Exercise)
    df = df[df['Exercise'] == closest_match]
    if df_pareto is not None:
        df_pareto = df_pareto[df_pareto['Exercise'] == closest_match]
    if df_targets is not None:
        df_targets = df_targets[df_targets['Exercise'] == closest_match]

    fig, ax = plt.subplots()

    if df_pareto is not None:
        pareto_points = list(zip(df_pareto['Reps'], df_pareto['Weight']))
        pareto_reps, pareto_weights = zip(*sorted(pareto_points, key=lambda x: x[0]))

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(pareto_weights, pareto_reps)]
        max_1rm = max(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min(df['Reps']), max(df['Reps']), 10)
        y_vals = [estimate_weight_from_1rm(max_1rm, r) for r in x_vals]
        ax.plot(x_vals, y_vals, 'k--', label='Max Achieved 1RM', alpha=0.7)

        ax.step(pareto_reps, pareto_weights, color='red', marker='o', label='Pareto Front')

    if df_targets is not None:
        target_points = list(zip(df_targets['Reps'], df_targets['Weight']))
        target_reps, target_weights = zip(*sorted(target_points, key=lambda x: x[0]))

        # Compute best 1RM from Pareto front
        one_rms = [calculate_1rm(w, r) for w, r in zip(target_weights, target_reps)]
        min_1rm = min(one_rms)

        # Generate dotted Epley decay line
        x_vals = np.linspace(min(df['Reps']), max(df['Reps']), 10)
        y_vals = [estimate_weight_from_1rm(min_1rm, r) for r in x_vals]
        ax.plot(x_vals, y_vals, 'g-.', label='Min Target 1RM', alpha=0.7)

        ax.scatter(df_targets['Reps'], df_targets['Weight'], color='green', marker='x', label='Targets')

    # Plotting
    ax.scatter(df['Reps'], df['Weight'], label='Data Points')

    ax.set_title(f"Weight vs. Reps for {closest_match}")
    ax.set_xlabel("Reps")
    ax.set_xlim(left=0)
    ax.set_ylabel("Weight")
    ax.legend()

    return fig

test_df = pd.DataFrame({
    'Exercise':['Bench Press']*6 + ['Flat Bench Press']*4,
    'Weight':[40, 100, 105, 85, 55, 15] + [95, 75, 45, 10],
    'Reps':  [ 4, 1,  1,  3, 6, 11] + [  1,  3, 5, 11],
  })
df_records = highest_weight_per_rep(test_df)
df_targets = dougs_next_pareto(df_records)
fig = plot_df(test_df, df_pareto=df_records, df_targets=df_targets, Exercise='Bench Press')


# Assuming 'Date' column exists and is in datetime format.
# If not, convert it first:
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d') # Example format, adjust as needed.

# Sort the DataFrame by 'Date' in ascending order (least recent to most recent)
df_sorted = df.sort_values(by='Date', ascending=True)

# Turn Distance into Weight?
df_sorted['Weight'] = df_sorted['Weight'].combine_first(df_sorted['Distance'])
df_sorted['Time'] = pd.to_timedelta(df_sorted['Time']).dt.total_seconds()/60
df_sorted['Reps'] = df_sorted['Reps'].combine_first(df_sorted['Time'])

# drop what we don't care about
df_sorted = df_sorted.drop(['Distance', 'Weight Unit', 'Distance Unit', 'Comment', 'Time'], axis=1)
df_sorted = df_sorted[df_sorted['Category'] != 'Cardio']
df_sorted = df_sorted[df_sorted['Exercise'] != 'Climbing']
df_sorted = df_sorted[df_sorted['Exercise'] != 'Tricep Push Ul']

df_records = highest_weight_per_rep(df_sorted)
df_targets = dougs_next_pareto(df_records)

fig = plot_df(df_sorted, Exercise='Curl Pulldown Bicep')
fig = plot_df(df_sorted, df_pareto=df_records, Exercise='Curl Pulldown Bicep')
fig = plot_df(df_sorted, df_records, df_targets, Exercise='Curl Pulldown Bicep')

fig = plot_df(df_sorted, df_records, df_targets, Exercise='Straight-Arm Cable Pushdown')

N_CAT = 2
N_EXERCISES_PER_CAT = 2
N_TARGET_SETS_PER_EXERCISES = 2

# Find the most recent date for each category
category_most_recent = df_sorted.groupby('Category')['Date'].max()

# Sort categories by their most recent date (oldest first)
sorted_categories = category_most_recent.sort_values().index
output_lines = []

for category in sorted_categories[:N_CAT]:  # Take the category with oldest most recent date
    print(f"{category=}")
    output_lines.append(f"Category: {category}\n")

    # Filter to this category
    category_df = df_sorted[df_sorted['Category'] == category]

    # Find the oldest exercises in this category
    exercise_oldest_dates = category_df.groupby('Exercise')['Date'].max()
    oldest_exercises = exercise_oldest_dates.nsmallest(N_EXERCISES_PER_CAT)

    for exercise, oldest_date in oldest_exercises.items():
        print(f"  {exercise=}, date={oldest_date}")
        output_lines.append(f"  Exercise: {exercise}, Last Done: {oldest_date}\n")

        # Find the lowest 3 sets to target
        sorted_exercise_targets = df_targets[df_targets['Exercise'] == exercise].nsmallest(n=N_TARGET_SETS_PER_EXERCISES, columns='1RM')
        for index, row in sorted_exercise_targets.iterrows():
            print(f"    {row['Weight']} for {row['Reps']} reps ({row['1RM']:.2f} 1rm)")
            output_lines.append(f"    {row['Weight']} lbs for {row['Reps']} reps ({row['1RM']:.2f} 1RM)\n")

    print(' ')
    output_lines.append("\n")  # Add a blank line between categories

# Save to file
output_file = working_dir+"workout_summary.txt"
with open(output_file, "w") as f:
    f.writelines(output_lines)

print(f"Saved to {output_file}")

import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Create a dictionary: { exercise_name: base64_image_string }
figures_html = {}
errors = ""
for exercise in df['Exercise'].unique():
    try:
        fig = plot_df(df_sorted, df_records, df_targets, Exercise=exercise)
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight')
        buf.seek(0)
        base64_img = base64.b64encode(buf.read()).decode('utf-8')
        img_html = f'<img src="data:image/png;base64,{base64_img}" id="fig-{exercise}" class="exercise-figure" style="display:none; max-width:100%; height:auto;">'
        figures_html[exercise] = img_html
        plt.close(fig)
    except Exception as e:
        errors += f"{e}"

all_figures_html = "\n".join(figures_html.values())

from IPython.display import display, HTML

# Basic setup
exercise_column = "Exercise"  # Adjust if needed
exercise_options = sorted(df_targets[exercise_column].dropna().unique())

# Build dropdown
dropdown_html = f"""
<label for="exerciseDropdown">Filter by Exercise:</label>
<select id="exerciseDropdown">
  <option value="">All</option>
  {''.join(f'<option value="{x}">{x}</option>' for x in exercise_options)}
</select>
<br><br>
"""

# Convert DataFrame to HTML table
table_html = df_targets.to_html(classes="display compact cell-border", table_id="exerciseTable", index=False)

# JS and CSS for DataTables + filtering
# JS, CSS, and styling improvements
js_and_css = """
<!-- DataTables -->
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>

<!-- Select2 for searchable dropdown -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<!-- Custom Styling for Mobile -->
<style>
  body {
    font-family: Arial, sans-serif;
    font-size: 34px;
    padding: 28px;
  }

  table.dataTable {
    font-size: 32px;
    width: 100% !important;
    word-wrap: break-word;
  }

  label, select {
    font-size: 34px;
  }

  #exerciseDropdown {
    width: 100%;
    max-width: 400px;
  }

  @media only screen and (max-width: 600px) {
    table, thead, tbody, th, td, tr {
      display: block;
    }
    th {
      text-align: left;
    }
  }
</style>

<script>
$(document).ready(function() {
    // Initialize DataTable
    var table = $('#exerciseTable').DataTable({
        responsive: true
    });

    // Initialize Select2 for searchable dropdown
    $('#exerciseDropdown').select2({
        placeholder: "Filter by Exercise",
        allowClear: true
    });

    // Filter by selected exercise
    $('#exerciseDropdown').on('change', function() {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(val ? '^' + val + '$' : '', true, false).draw(); // assumes Exercise is col 0
    });

    $('#exerciseDropdown').on('change', function() {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();

        // Hide all figures
        $('.exercise-figure').hide();

        // Show the matching figure
        if (this.value) {
            $('#fig-' + this.value).show();
        }
    });
});
</script>
"""

# Final combo
full_html = js_and_css + dropdown_html + table_html + all_figures_html
display(HTML(full_html))

# --- Save the HTML to a file ---
with open(working_dir+"interactive_table.html", 'w', encoding='utf-8') as f:
    f.write(full_html)