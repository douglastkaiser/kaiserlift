# Data Preprocessing Scripts

This directory contains scripts for optimizing CSV data loading performance.

## `preprocess_data.py`

Pre-processes raw CSV data files to create optimized versions for fast webpage loading.

### Features

Implements three optimization strategies:

1. **Filtered CSV** - Creates `data/lifting_filtered.csv` and `data/running_filtered.csv`
   - Removes unnecessary columns (Comment, Distance Unit, etc.)
   - Filters out non-lifting exercises (Cardio, Climbing, etc.)
   - Maintains human-readable CSV format
   - Reduces file size by ~30-50%

2. **Pareto JSON** - Creates `data/pareto_data.json`
   - Pre-calculates Pareto-optimal sets (highest weight per rep count)
   - Includes 1RM calculations and next target recommendations
   - Reduces data from ~3,700 rows to ~50-200 Pareto points
   - JSON format for fast JavaScript loading
   - Reduces data transfer by ~90%+

3. **Statistics JSON** - Creates `data/stats.json`
   - Summary metadata (exercise list, date ranges, row counts)
   - Used for quick info display without loading full datasets

### Usage

**Manual execution:**
```bash
uv run python scripts/preprocess_data.py
```

**Automatic execution:**
- Runs automatically in CI/CD before HTML generation
- See `.github/workflows/main.yml` for integration

### Input Files

- `data/lifting.csv` - Raw FitNotes export for lifting exercises
- `data/running.csv` - Running/cardio data

### Output Files

- `data/lifting_filtered.csv` - Filtered lifting data
- `data/running_filtered.csv` - Filtered running data
- `data/pareto_data.json` - Pre-calculated Pareto fronts
- `data/stats.json` - Summary statistics

### Performance Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Data transferred | ~210 KB | ~20 KB | 90% reduction |
| Rows processed | ~3,700 | ~150 | 96% reduction |
| Webpage load time | High | Low | Significantly faster |
| Processing location | Client-side | Build-time | No client overhead |

### Integration with HTML Generation

The `generate_example_html.py` script automatically uses pre-filtered data when available:

1. Checks for `data/lifting_filtered.csv` (fastest)
2. Falls back to `data/lifting.csv` (processes on-the-fly)
3. Falls back to example CSVs (last resort)

This enables optimal performance in production while maintaining development flexibility.

## Other Scripts

### `inject_version.py`

Injects the current package version into client-side JavaScript files.
