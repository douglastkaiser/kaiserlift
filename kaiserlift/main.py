import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from IPython.display import display, HTML

from helpers import dougs_next_pareto, highest_weight_per_rep, plot_df

# Get a list of all CSV files in the current directory
working_dir = "/content/drive/MyDrive/Personal Work/Workout Analysis (90%)/"
csv_files = glob.glob(working_dir + "FitNotes_Export_*.csv")

# Find the file with the most recent timestamp
latest_file = max(csv_files, key=os.path.getctime)
print(f"Using {latest_file}")

# Load the latest file into a pandas DataFrame
df = pd.read_csv(latest_file)


test_df = pd.DataFrame(
    {
        "Exercise": ["Bench Press"] * 6 + ["Flat Bench Press"] * 4,
        "Weight": [40, 100, 105, 85, 55, 15] + [95, 75, 45, 10],
        "Reps": [4, 1, 1, 3, 6, 11] + [1, 3, 5, 11],
    }
)
df_records = highest_weight_per_rep(test_df)
df_targets = dougs_next_pareto(df_records)
fig = plot_df(
    test_df, df_pareto=df_records, df_targets=df_targets, Exercise="Bench Press"
)


# Assuming 'Date' column exists and is in datetime format.
# If not, convert it first:
df["Date"] = pd.to_datetime(
    df["Date"], format="%Y-%m-%d"
)  # Example format, adjust as needed.

# Sort the DataFrame by 'Date' in ascending order (least recent to most recent)
df_sorted = df.sort_values(by="Date", ascending=True)

# Turn Distance into Weight?
df_sorted["Weight"] = df_sorted["Weight"].combine_first(df_sorted["Distance"])
df_sorted["Time"] = pd.to_timedelta(df_sorted["Time"]).dt.total_seconds() / 60
df_sorted["Reps"] = df_sorted["Reps"].combine_first(df_sorted["Time"])

# drop what we don't care about
df_sorted = df_sorted.drop(
    ["Distance", "Weight Unit", "Distance Unit", "Comment", "Time"], axis=1
)
df_sorted = df_sorted[df_sorted["Category"] != "Cardio"]
df_sorted = df_sorted[df_sorted["Exercise"] != "Climbing"]
df_sorted = df_sorted[df_sorted["Exercise"] != "Tricep Push Ul"]

df_records = highest_weight_per_rep(df_sorted)
df_targets = dougs_next_pareto(df_records)

fig = plot_df(df_sorted, Exercise="Curl Pulldown Bicep")
fig = plot_df(df_sorted, df_pareto=df_records, Exercise="Curl Pulldown Bicep")
fig = plot_df(df_sorted, df_records, df_targets, Exercise="Curl Pulldown Bicep")

fig = plot_df(df_sorted, df_records, df_targets, Exercise="Straight-Arm Cable Pushdown")

N_CAT = 2
N_EXERCISES_PER_CAT = 2
N_TARGET_SETS_PER_EXERCISES = 2

# Find the most recent date for each category
category_most_recent = df_sorted.groupby("Category")["Date"].max()

# Sort categories by their most recent date (oldest first)
sorted_categories = category_most_recent.sort_values().index
output_lines = []

for category in sorted_categories[
    :N_CAT
]:  # Take the category with oldest most recent date
    print(f"{category=}")
    output_lines.append(f"Category: {category}\n")

    # Filter to this category
    category_df = df_sorted[df_sorted["Category"] == category]

    # Find the oldest exercises in this category
    exercise_oldest_dates = category_df.groupby("Exercise")["Date"].max()
    oldest_exercises = exercise_oldest_dates.nsmallest(N_EXERCISES_PER_CAT)

    for exercise, oldest_date in oldest_exercises.items():
        print(f"  {exercise=}, date={oldest_date}")
        output_lines.append(f"  Exercise: {exercise}, Last Done: {oldest_date}\n")

        # Find the lowest 3 sets to target
        sorted_exercise_targets = df_targets[
            df_targets["Exercise"] == exercise
        ].nsmallest(n=N_TARGET_SETS_PER_EXERCISES, columns="1RM")
        for index, row in sorted_exercise_targets.iterrows():
            print(f"    {row['Weight']} for {row['Reps']} reps ({row['1RM']:.2f} 1rm)")
            output_lines.append(
                f"    {row['Weight']} lbs for {row['Reps']} reps ({row['1RM']:.2f} 1RM)\n"
            )

    print(" ")
    output_lines.append("\n")  # Add a blank line between categories

# Save to file
output_file = working_dir + "workout_summary.txt"
with open(output_file, "w") as f:
    f.writelines(output_lines)

print(f"Saved to {output_file}")


# Create a dictionary: { exercise_name: base64_image_string }
figures_html = {}
errors = ""
for exercise in df["Exercise"].unique():
    try:
        fig = plot_df(df_sorted, df_records, df_targets, Exercise=exercise)
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        base64_img = base64.b64encode(buf.read()).decode("utf-8")
        img_html = f'<img src="data:image/png;base64,{base64_img}" id="fig-{exercise}" class="exercise-figure" style="display:none; max-width:100%; height:auto;">'
        figures_html[exercise] = img_html
        plt.close(fig)
    except Exception as e:
        errors += f"{e}"

all_figures_html = "\n".join(figures_html.values())

# Basic setup
exercise_column = "Exercise"  # Adjust if needed
exercise_options = sorted(df_targets[exercise_column].dropna().unique())

# Build dropdown
dropdown_html = f"""
<label for="exerciseDropdown">Filter by Exercise:</label>
<select id="exerciseDropdown">
  <option value="">All</option>
  {"".join(f'<option value="{x}">{x}</option>' for x in exercise_options)}
</select>
<br><br>
"""

# Convert DataFrame to HTML table
table_html = df_targets.to_html(
    classes="display compact cell-border", table_id="exerciseTable", index=False
)

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
with open(working_dir + "interactive_table.html", "w", encoding="utf-8") as f:
    f.write(full_html)
