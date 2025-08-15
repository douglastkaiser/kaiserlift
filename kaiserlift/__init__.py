from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kaiserlift")
except PackageNotFoundError:  # pragma: no cover - fallback for dev environments
    from pathlib import Path
    import tomllib

    _pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with _pyproject.open("rb") as _f:
        __version__ = tomllib.load(_f)["project"]["version"]

try:
    from .viewers import (
        get_closest_exercise,
        plot_df,
        print_oldest_exercise,
        gen_html_viewer,
    )

    from .df_processers import (
        calculate_1rm,
        highest_weight_per_rep,
        estimate_weight_from_1rm,
        add_1rm_column,
        df_next_pareto,
        assert_frame_equal,
        import_fitnotes_csv,
        process_csv_files,
    )

    from .pipeline import pipeline
except ModuleNotFoundError:  # pragma: no cover - allow __version__ without deps
    pass

__all__ = [
    "calculate_1rm",
    "highest_weight_per_rep",
    "estimate_weight_from_1rm",
    "add_1rm_column",
    "df_next_pareto",
    "get_closest_exercise",
    "plot_df",
    "assert_frame_equal",
    "print_oldest_exercise",
    "import_fitnotes_csv",
    "process_csv_files",
    "gen_html_viewer",
    "pipeline",
]
