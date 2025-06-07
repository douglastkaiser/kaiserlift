from kaiserlift import (
    df_next_pareto,
    highest_weight_per_rep,
    plot_df,
    print_oldest_excercise,
    import_fitnotes_csv,
    gen_html_viewer,
)
from IPython.display import display, HTML
import glob
import os

os.makedirs("build", exist_ok=True)

# Get a list of all CSV files in the current directory
csv_files = glob.glob("FitNotes_Export_*.csv")

df = import_fitnotes_csv(csv_files)

df_records = highest_weight_per_rep(df)
df_targets = df_next_pareto(df_records)

fig = plot_df(df, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep.png")

fig = plot_df(df, df_pareto=df_records, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep Pareto.png")

fig = plot_df(df, df_records, df_targets, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep Pareto and Targets.png")

# Console print out with optional args
output_lines = print_oldest_excercise(
    df, n_cat=2, n_exercises_per_cat=2, n_target_sets_per_exercises=2
)
with open("build/your_workout_summary.txt", "w") as f:
    f.writelines(output_lines)

# HTML viewer
full_html = gen_html_viewer(df)
with open("build/your_interactive_table.html", "w", encoding="utf-8") as f:
    f.write(full_html)

# Console view
display(HTML(full_html))
