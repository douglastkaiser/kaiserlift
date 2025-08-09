from .df_processers import (
    calculate_1rm,
    highest_weight_per_rep,
    estimate_weight_from_1rm,
    add_1rm_column,
    df_next_pareto,
    assert_frame_equal,
    import_fitnotes_csv,
)

# Import viewer utilities if their heavy dependencies are installed.  These
# functions are optional; the core dataframe processing helpers above should be
# available even in minimal environments.  Previously importing this package
# would fail when `matplotlib` (an optional dependency of the viewers module)
# was missing.  To keep the lightweight parts usable we try to import the
# viewer helpers but silently ignore missing optional dependencies.
__all__ = [
    "calculate_1rm",
    "highest_weight_per_rep",
    "estimate_weight_from_1rm",
    "add_1rm_column",
    "df_next_pareto",
    "assert_frame_equal",
    "import_fitnotes_csv",
]

try:  # pragma: no cover - exercised in tests via successful import
    from .viewers import (
        get_closest_exercise,
        plot_df,
        print_oldest_excercise,
        gen_html_viewer,
    )
except ModuleNotFoundError:  # viewers require optional plotting libraries
    # The optional viewer utilities are unavailable.  Users attempting to use
    # them will see an ImportError when importing `kaiserlift.viewers`
    # directly; the core dataframe helpers remain usable.
    pass
else:  # Only expose viewer helpers when import succeeds
    __all__ += [
        "get_closest_exercise",
        "plot_df",
        "print_oldest_excercise",
        "gen_html_viewer",
    ]
