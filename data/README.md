# Personal Data Directory

This directory contains your personal CSV files that will be pre-processed into the website at build time.

## File Structure

- `lifting.csv` - Your FitNotes lifting data export
- `running.csv` - Your running pace data

## CSV Format

### Lifting Data (lifting.csv)
Expected columns:
- Date
- Exercise
- Category
- Weight
- Reps

### Running Data (running.csv)
Expected columns:
- Date
- Exercise
- Category
- Distance (miles)
- Duration (minutes)

Note: Pace (seconds/mile) is automatically calculated from Duration and Distance during processing.

## Usage

1. Export your data from FitNotes or your tracking app
2. Place the files in this directory as `lifting.csv` and `running.csv`
3. The build process will automatically generate the website with your data
4. Commit and push to update the live website

## Privacy

By default, CSV files in this directory are tracked in git. If you want to keep your data private:
1. Add `data/*.csv` to `.gitignore`
2. Use environment variables or secrets to populate data during CI/CD

The upload feature on the website will still work for ad-hoc updates!
