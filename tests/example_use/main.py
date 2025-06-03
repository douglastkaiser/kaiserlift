import glob

from kaiserlift import (
    dougs_next_pareto,
    highest_weight_per_rep,
    plot_df,
    print_oldest_excercise,
    import_fitnotes_csv,
    gen_html_viewer,
)

# Get a list of all CSV files in the current directory
csv_files = glob.glob("FitNotes_Export_*.csv")

df_sorted = import_fitnotes_csv(csv_files)

df_records = highest_weight_per_rep(df_sorted)
df_targets = dougs_next_pareto(df_records)

fig = plot_df(df_sorted, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep.png")

fig = plot_df(df_sorted, df_pareto=df_records, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep Pareto.png")

fig = plot_df(df_sorted, df_records, df_targets, Exercise="Curl Pulldown Bicep")
fig.savefig("build/Curl Pulldown Bicep Pareto and Targets.png")

print_oldest_excercise(df_sorted)

gen_html_viewer(df_sorted)
