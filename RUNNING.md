# Running Data Feature

KaiserLift now supports running/cardio data analysis with the same Pareto front optimization approach used for lifting data!

## Features

- **Upload running data** with distance and pace metrics
- **Pareto front visualization** showing your best pace at each distance
- **Target recommendations** for improving your running performance
- **Race pace predictions** - predict your target pace for upcoming races (e.g., 5K, 10K, half marathon)
- **Progress tracking** over time with interactive plots

## CSV Format

The running data CSV should have these columns:

```csv
Date,Exercise,Category,Distance (miles),Duration (minutes)
2024-01-15,Running,Cardio,5.0,47.5
```

### Required Columns:
- **Date**: YYYY-MM-DD format
- **Exercise**: Exercise name (e.g., "Running", "Cycling")
- **Category**: Must be "Cardio"
- **Distance (miles)**: Distance in miles
- **Duration (minutes)**: Total time in minutes

**Note**: Pace (seconds/mile) is automatically calculated from Duration and Distance. You don't need to provide Pace, Cadence, or Comments - just the essential data: distance and total time.

## How It Works

### 1. Pareto Front Analysis

The system identifies your **Pareto-optimal performances** - runs that aren't dominated by any other run. A run is dominated if there exists another run that is:
- **Longer distance** with **same or faster pace** (equivalently: same or higher speed)

For example:
- 5 miles @ 9:30 pace (6.32 mph) ✅ (Pareto optimal)
- 10 miles @ 10:00 pace (6.00 mph) ✅ (Pareto optimal - longer but slower is OK)
- 3 miles @ 10:00 pace (6.00 mph) ❌ (Dominated by 5 @ 9:30 - shorter and slower)

The Pareto front is visualized on a Distance vs Speed plot, where better performances are toward the **upper-right** (longer distance + faster speed), matching the lifting visualization.

### 2. Pace Prediction Model

Unlike lifting's 1RM formula (Epley), running uses an **aerobic degradation model**:

```
pace_at_distance = best_pace × (1 + 0.05 × (distance_ratio - 1))
```

This models how your pace naturally slows down as distance increases (~5% slower per doubling of distance).

### 3. Target Generation

The system generates three types of training targets:

1. **Speed work**: Run your shortest Pareto distance 5% faster
2. **Gap fillers**: Add 0.5-mile increments between existing Pareto points
3. **Distance progression**: Add 0.5 miles to your longest run

### 4. Race Pace Prediction

Given your Pareto front, the system can predict your target pace for any race distance:

```python
from kaiserlift import predict_race_pace, highest_pace_per_distance, process_running_csv_files

# Load your data
df = process_running_csv_files(['running_data.csv'])
records = highest_pace_per_distance(df)

# Predict 5K pace (3.1 miles)
prediction = predict_race_pace(records, "Running", 3.1)

print(f"Optimistic 5K pace: {prediction['optimistic_pace_str']} per mile")
print(f"Conservative 5K pace: {prediction['conservative_pace_str']} per mile")
print(f"Predicted 5K time: {prediction['optimistic_time']}")
```

## Usage

### Web Interface

1. Start the server:
   ```bash
   python -m kaiserlift.webapp
   ```

2. Navigate to `http://localhost:8000`

3. Use the "Upload Running Data" form to upload your CSV

4. View your Pareto front, targets, and interactive plots

### Python API

```python
from kaiserlift import running_pipeline

# Generate HTML report
html = running_pipeline(['my_running_data.csv'])

# Save to file
with open('running_report.html', 'w') as f:
    f.write(html)
```

### Individual Functions

```python
from kaiserlift import (
    process_running_csv_files,
    highest_pace_per_distance,
    df_next_running_targets,
    estimate_pace_at_distance,
    predict_race_pace,
)

# Load and process data
df = process_running_csv_files(['data.csv'])

# Get Pareto front (your PRs)
pareto_records = highest_pace_per_distance(df)

# Generate training targets
targets = df_next_running_targets(pareto_records)

# Estimate pace at different distance
# If you ran 5 miles @ 9:30 pace, what pace for 10 miles?
pace_10mi = estimate_pace_at_distance(
    best_pace=570,      # 9:30 in seconds
    best_distance=5.0,
    target_distance=10.0
)

# Predict race pace
race_prediction = predict_race_pace(pareto_records, "Running", 3.1)  # 5K
```

## Example: Training for a 5K

Let's say you want to run a 5K (3.1 miles) and your current PRs are:

- 3.0 miles @ 9:00 pace
- 5.0 miles @ 9:30 pace
- 10.0 miles @ 10:00 pace

The system will:

1. **Identify your Pareto front**: All three runs are Pareto-optimal
2. **Predict your 5K pace**: Based on your 3-mile and 5-mile times
   - Optimistic: ~9:05 per mile → 28:15 total time
   - Conservative: ~9:20 per mile → 29:00 total time
3. **Suggest targets**:
   - Speed work: Run 3.0 miles @ 8:33 pace (5% faster)
   - Distance: Run 10.5 miles @ 10:00 pace
   - Fill gaps: Run 3.5, 4.0, 4.5 miles at estimated paces

## Visualization

The HTML output includes:

- **Interactive table** of training targets (sortable, searchable)
- **Pareto front plot** showing Distance vs Speed
  - Blue dots: All your runs
  - Red line: Your Pareto front (best speeds)
  - Black dashed line: Predicted speed curve
  - Green X markers: Recommended training targets
  - **Better performance is upper-right**: longer distance + faster speed
- **Dropdown filter** to view specific exercises
- **Dark mode support**

## Differences from Lifting

| Aspect | Lifting | Running |
|--------|---------|---------|
| Primary Metric | Weight (↑ better) | Distance (↑ better) |
| Secondary Metric | Reps (↑ better) | Speed (↑ better) |
| Formula | Epley 1RM | Aerobic degradation |
| Pareto Logic | Higher weight + reps | Longer distance + faster speed |
| Pareto Direction | Upper-right is better | Upper-right is better |
| Target Increment | +5 lbs, +1 rep | +0.5 miles, +5% speed |

## Sample Data

See `tests/example_use/running_sample.csv` for a complete example with 15 runs showing progression from 3-mile to half-marathon distances.

## Tips

- **Consistent units**: Make sure all distances are in the same unit (miles or km)
- **Duration format**: Use decimal minutes (e.g., 47.5 for 47 minutes 30 seconds)
- **Track progression**: Upload data regularly to see your Pareto front expand
- **Mix distances**: Run various distances to build a complete Pareto front
- **Use predictions**: Before a race, check your predicted pace to set realistic goals

## Future Enhancements

Potential future features:
- Support for different race distances (marathon, ultra)
- Heart rate zone analysis
- Elevation adjustment for pace
- Training plan generation
- Historical progression tracking
