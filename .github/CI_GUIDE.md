# CI/CD Development Guide

This guide explains how to use KaiserLift's comprehensive CI/CD system for development, testing, and deployment.

## Overview

The CI system is designed to enable **full development and evaluation within CI**, allowing you to:
- ✅ Test branches comprehensively before merging
- 📊 Get detailed evaluation reports automatically
- 🌐 Preview changes with live deployments
- ⚡ Track performance with benchmarks
- 📈 Monitor code quality and coverage

## Workflows

### 1. Main CI Workflow (`main.yml`)

**Triggers:** Every push to any branch

**What it does:**
- Runs linting with Ruff
- Tests on Python 3.12 and 3.13 (matrix)
- Measures test coverage
- Tests the built wheel installation
- Generates example HTML files
- Deploys to GitHub Pages (main branch only)

**Artifacts:**
- `coverage-report` - Coverage data (Python 3.12 only)
- `github-pages` - Example HTML files

**Use this for:** Continuous validation of all commits

---

### 2. Branch Evaluation Workflow (`branch-evaluation.yml`)

**Triggers:**
- Automatically on PRs (opened, synchronized, reopened)
- Automatically on non-main branch pushes
- Manually via GitHub Actions UI

**What it does:**
Creates a comprehensive evaluation bundle containing:
- 📦 Built Python wheel
- 🧪 Full test results with coverage (HTML + JSON)
- ⚡ Performance benchmark results
- 📊 Code quality metrics (linting stats, LOC)
- 🌐 Interactive HTML examples (lifting + running)
- 🔍 Comparison with main branch (diff stats, file changes)

**Artifacts:**
- `evaluation-bundle-{sha}` - Complete evaluation package

**Use this for:** Thorough branch review before merging

#### Manual Trigger

Go to Actions → Branch Evaluation → Run workflow:
- Select branch
- Choose Python version (default: 3.12)

#### Evaluation Bundle Contents

```
evaluation_bundle/
├── README.md                    # Guide to the bundle
├── *.whl                       # Built wheel (pip installable)
├── test_results.txt            # Full test output
├── coverage_html/              # Interactive coverage report
│   └── index.html             # Open this in browser
├── coverage.json               # Coverage data (JSON)
├── benchmark_results.json      # Detailed benchmarks
├── benchmark_output.txt        # Human-readable benchmarks
├── ruff_check.json             # Linting results
├── ruff_stats.txt              # Linting statistics
├── metrics.md                  # Code metrics
├── html_examples/              # Generated examples
│   ├── index.html             # Lifting example
│   └── running/index.html     # Running example
└── comparison.md               # Diff vs main branch
```

---

### 3. Preview Deployment Workflow (`preview-deployment.yml`)

**Triggers:** Pull requests (opened, synchronized, reopened)

**What it does:**
- Generates HTML examples for the PR branch
- Deploys to `pr-{number}/` directory on gh-pages
- Posts comment with preview links
- Updates comment on each push

**Artifacts:**
- `preview-pr-{number}` - Preview HTML files

**Preview URLs:**
- Lifting: `https://{owner}.github.io/{repo}/pr-{number}/index.html`
- Running: `https://{owner}.github.io/{repo}/pr-{number}/running/index.html`

**Use this for:** Sharing live demos with reviewers

#### If GitHub Pages is not enabled:
The workflow still works! It uploads artifacts that you can download and view locally.

---

### 4. PR Comment Bot (`pr-comment.yml`)

**Triggers:** When Branch Evaluation completes on a PR

**What it does:**
Automatically posts a comment on the PR with:
- ✅/❌ Test pass/fail status
- 🟢🟡🔴 Coverage percentage
- 📦 Wheel size
- ⚡ Benchmark availability
- 🔗 Links to download evaluation bundle

**Use this for:** Quick PR health checks

---

### 5. Build Client Wheel (`build-client-wheel.yml`)

**Triggers:** Pushes to main + PRs

**What it does:**
- Builds the wheel
- Uploads as `client-wheel` artifact

**Use this for:** Accessing built wheels for testing

---

### 6. Publish Workflow (`publish.yml`)

**Triggers:** Pushes to main branch (after PRs merge)

**What it does:**
- Auto-bumps patch version
- Builds wheel
- Publishes to PyPI

**Use this for:** Automatic releases

---

## Development Workflows

### Scenario 1: Feature Development

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and push:**
   ```bash
   git push origin feature/my-feature
   ```

3. **Automatic evaluation:**
   - Branch Evaluation runs automatically
   - Download evaluation bundle from Actions tab
   - Review coverage, benchmarks, examples

4. **Create PR:**
   - Preview Deployment creates live demo
   - PR Comment Bot posts results
   - Share preview URL with reviewers

5. **Iterate:**
   - Each push updates preview
   - Each push creates new evaluation bundle
   - Comment updates with latest metrics

### Scenario 2: Quick Testing

**Manual evaluation without PR:**

1. Go to Actions → Branch Evaluation
2. Click "Run workflow"
3. Select your branch
4. Download evaluation bundle
5. Install wheel locally: `pip install *.whl`

### Scenario 3: Performance Testing

1. **Run benchmarks locally:**
   ```bash
   pytest tests/test_benchmarks.py --benchmark-only -v
   ```

2. **Compare with CI:**
   - Check evaluation bundle `benchmark_results.json`
   - Compare times between branches

3. **Track regressions:**
   - Benchmark data saved in each evaluation
   - Compare JSON between commits

### Scenario 4: Coverage Improvement

1. **Check current coverage:**
   - Look at PR comment
   - Download `coverage_html/` from evaluation bundle
   - Open `index.html` in browser

2. **Identify gaps:**
   - Red/yellow highlighting shows uncovered code
   - Focus on critical paths

3. **Add tests:**
   - Write new tests
   - Push and check updated coverage

---

## Artifacts Guide

### How to Download Artifacts

1. Go to repository → Actions tab
2. Click on a workflow run
3. Scroll to "Artifacts" section
4. Click artifact name to download

### Artifact Retention

- Evaluation bundles: 30 days
- Preview deployments: 30 days
- Coverage reports: 90 days (default)
- GitHub Pages: Permanent (until redeployed)

---

## Configuration

### Test Coverage

Edit `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["kaiserlift"]
omit = ["*/tests/*"]

[tool.coverage.report]
precision = 2
show_missing = true
```

### Benchmarks

Add new benchmarks to `tests/test_benchmarks.py`:
```python
def test_benchmark_my_function(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result == expected
```

### Matrix Testing

Edit `.github/workflows/main.yml`:
```yaml
strategy:
  matrix:
    python-version: ['3.12', '3.13', '3.14']  # Add versions
```

---

## Best Practices

### For Contributors

1. **Always check evaluation bundle before requesting review**
   - Ensure tests pass
   - Verify coverage didn't drop
   - Review benchmarks for regressions

2. **Use preview deployments**
   - Share preview links in PR description
   - Test on different devices/browsers

3. **Monitor PR comments**
   - Green coverage = good
   - Address test failures immediately

### For Reviewers

1. **Check preview deployment first**
   - Visual verification is fast
   - Test actual functionality

2. **Download evaluation bundle**
   - Review test coverage
   - Check benchmark changes
   - Examine code quality metrics

3. **Compare with main**
   - Use `comparison.md` in bundle
   - Look for unexpected changes

---

## Troubleshooting

### Evaluation Bundle Missing

**Problem:** Can't find evaluation-bundle artifact

**Solution:**
- Check if workflow completed (may take 2-5 min)
- Look for `evaluation-bundle-{sha}` (not just "evaluation-bundle")
- Verify branch triggered the workflow (non-main branches + PRs)

### Preview Deployment 404

**Problem:** Preview URL returns 404

**Solution:**
1. Check if GitHub Pages is enabled (Settings → Pages)
2. Verify workflow completed successfully
3. Try `https://{owner}.github.io/{repo}/pr-{number}/index.html`
4. If Pages disabled, download artifact instead

### Tests Pass Locally but Fail in CI

**Problem:** Tests work on my machine but not in CI

**Solution:**
1. Check Python version (CI uses matrix)
2. Verify all dependencies in `pyproject.toml`
3. Look for environment-specific code
4. Run tests with same Python version locally

### Coverage Dropped Unexpectedly

**Problem:** Coverage decreased but I added tests

**Solution:**
1. Check if you added new uncovered code
2. Verify tests are running (not skipped)
3. Review `coverage_html/` to see exact gaps
4. Ensure `--cov=kaiserlift` includes new modules

---

## Advanced Usage

### Running Full Evaluation Locally

Replicate CI evaluation on your machine:

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests with coverage
pytest tests \
  --cov=kaiserlift \
  --cov-report=html \
  --cov-report=term \
  --benchmark-skip

# Run benchmarks
pytest tests/test_benchmarks.py --benchmark-only -v

# Generate examples
python tests/example_use/generate_example_html.py

# Build wheel
uv build

# Lint
uvx ruff check .
```

### Custom Evaluation

Create custom workflow for special testing:

```yaml
name: Custom Evaluation
on: workflow_dispatch

jobs:
  custom:
    runs-on: ubuntu-latest
    steps:
      # Your custom steps
      - name: Custom test
        run: # your commands
```

---

## FAQ

**Q: How long do workflows take?**
A: Main CI: ~2-3 min, Branch Evaluation: ~3-5 min, Preview: ~2 min

**Q: Can I cancel running workflows?**
A: Yes! Go to Actions → Running workflow → Cancel

**Q: Do all workflows run on every push?**
A: Main CI runs always. Branch Evaluation runs on non-main branches. Preview only on PRs.

**Q: How much does this cost?**
A: Free for public repos. Private repos use GitHub Actions minutes (2000/month free).

**Q: Can I run workflows manually?**
A: Yes! Branch Evaluation has manual trigger. Others can be added with `workflow_dispatch`.

---

## Summary

KaiserLift's CI system provides:

✅ **Automated Testing** - Every commit tested on multiple Python versions
📊 **Comprehensive Evaluation** - Full bundle with tests, coverage, benchmarks
🌐 **Live Previews** - Interactive demos for every PR
⚡ **Performance Tracking** - Benchmark suite for regression detection
🤖 **Smart Comments** - Automatic PR status updates
📈 **Quality Metrics** - Coverage, linting, code stats

**Result:** You can develop, test, and review entirely within CI, with rich artifacts for evaluation.
