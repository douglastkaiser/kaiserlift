from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kaiserlift")
except PackageNotFoundError:  # pragma: no cover - fallback for dev environments
    try:
        from setuptools_scm import get_version
        from pathlib import Path

        _root = Path(__file__).resolve().parent.parent
        __version__ = get_version(root=_root)
    except Exception:
        __version__ = "0.0.0.dev0"

try:
    from .viewers import (
        get_closest_exercise,
        plot_df,
        plot_df_1rm,
        plot_df_combined,
        print_oldest_exercise,
        gen_html_viewer,
    )

    from .df_processers import (
        calculate_1rm,
        highest_weight_per_rep,
        highest_1rm_per_rep,
        estimate_weight_from_1rm,
        add_1rm_column,
        df_next_pareto,
        assert_frame_equal,
        import_fitnotes_csv,
        process_csv_files,
    )

    from .pipeline import pipeline

    from .running_viewers import (
        plot_running_df,
        plot_running_pace_df,
        plot_running_combined,
        gen_running_html_viewer,
    )

    from .running_processers import (
        highest_pace_per_distance,
        highest_pace_per_distance_pace_pareto,
        estimate_pace_at_distance,
        add_speed_metric_column,
        df_next_running_targets,
        process_running_csv_files,
        calculate_pace_from_duration,
        seconds_to_pace_string,
        predict_race_pace,
    )

    from .running_pipeline import running_pipeline
except ModuleNotFoundError:  # pragma: no cover - allow __version__ without deps
    pass

__all__ = [
    # Lifting functions
    "calculate_1rm",
    "highest_weight_per_rep",
    "highest_1rm_per_rep",
    "estimate_weight_from_1rm",
    "add_1rm_column",
    "df_next_pareto",
    "get_closest_exercise",
    "plot_df",
    "plot_df_1rm",
    "plot_df_combined",
    "assert_frame_equal",
    "print_oldest_exercise",
    "import_fitnotes_csv",
    "process_csv_files",
    "gen_html_viewer",
    "pipeline",
    # Running functions
    "running_pipeline",
    "process_running_csv_files",
    "highest_pace_per_distance",
    "highest_pace_per_distance_pace_pareto",
    "estimate_pace_at_distance",
    "add_speed_metric_column",
    "df_next_running_targets",
    "plot_running_df",
    "plot_running_pace_df",
    "plot_running_combined",
    "gen_running_html_viewer",
    "calculate_pace_from_duration",
    "seconds_to_pace_string",
    "predict_race_pace",
]
