# CI Quick Reference

## 🚀 Quick Actions

### Run Full Evaluation on Any Branch
```
1. Go to: Actions → Branch Evaluation → Run workflow
2. Select: Your branch
3. Download: evaluation-bundle-{sha} artifact
```

### Get Live Preview for PR
```
1. Create PR (preview auto-deploys)
2. Check PR comment for preview links
3. Or download: preview-pr-{number} artifact
```

### Check Test Coverage
```
1. Look at PR comment (auto-posted)
2. Or download: coverage-report artifact from Main CI
3. Or download evaluation bundle → open coverage_html/index.html
```

### Run Benchmarks
```bash
# Locally
pytest tests/test_benchmarks.py --benchmark-only -v

# In CI: automatically included in evaluation bundle
```

---

## 📊 Workflows at a Glance

| Workflow | Trigger | Duration | Key Outputs |
|----------|---------|----------|-------------|
| **Main CI** | Every push | ~2-3 min | Tests on Py3.12+3.13, Coverage, Linting |
| **Branch Evaluation** | PRs, non-main pushes, manual | ~3-5 min | Complete bundle with tests, coverage, benchmarks, examples |
| **Preview Deployment** | PRs only | ~2 min | Live preview at `pr-{number}/` |
| **PR Comment Bot** | After evaluation | ~30 sec | Auto comment with metrics |
| **Publish** | Push to main | ~2 min | PyPI release + version bump |

---

## 📦 Artifacts Cheat Sheet

### evaluation-bundle-{sha}
**Contains:** Everything you need for branch review
- ✅ Tests results + coverage HTML
- ⚡ Benchmarks
- 📊 Code metrics
- 🌐 HTML examples
- 🔍 Diff vs main

**Get it from:** Branch Evaluation workflow

### preview-pr-{number}
**Contains:** HTML examples for the PR
- Lifting example
- Running example

**Get it from:** Preview Deployment workflow

### coverage-report
**Contains:** coverage.xml
**Get it from:** Main CI workflow (Python 3.12 only)

---

## 🎯 Common Workflows

### Before Requesting Review
1. ✅ Push your changes
2. ✅ Wait for Main CI (green checks)
3. ✅ Download evaluation bundle
4. ✅ Review: coverage, benchmarks, examples
5. ✅ Share preview link in PR description

### Reviewing a PR
1. 👀 Check preview deployment (click link in comment)
2. 📊 Check PR comment metrics (coverage, tests)
3. 📥 Download evaluation bundle
4. 🔍 Review coverage HTML and comparison.md

### Debugging CI Failures
1. 🔍 Check Actions tab → Failed workflow
2. 📖 Read error logs
3. 🧪 Run tests locally with same Python version
4. 🔄 Push fix, repeat

---

## 🛠️ Local Testing (Match CI)

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests like CI
pytest tests --cov=kaiserlift --cov-report=html --benchmark-skip -v

# Run benchmarks
pytest tests/test_benchmarks.py --benchmark-only -v

# Lint
uvx ruff check .
uvx ruff format .

# Build
uv build

# Generate examples
python tests/example_use/generate_example_html.py
```

---

## 🔗 Quick Links

- **Full Guide:** [CI_GUIDE.md](CI_GUIDE.md)
- **Workflows:** `.github/workflows/`
- **Actions Tab:** `https://github.com/{owner}/{repo}/actions`

---

## 💡 Pro Tips

1. **Manual evaluation:** Use "Run workflow" for ad-hoc testing without creating PR
2. **Preview before PR:** Preview deployment only works on PRs, but you can download artifact
3. **Coverage trends:** Compare coverage.json between branches
4. **Fast feedback:** PR comment updates on every push
5. **Wheel testing:** Install wheel from bundle to test exactly what gets published

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't find artifact | Wait for workflow to complete (~2-5 min) |
| Preview 404 | Enable GitHub Pages in Settings → Pages |
| Tests pass locally, fail CI | Check Python version matrix (3.12 vs 3.13) |
| Coverage dropped | Open coverage_html/index.html to see gaps |
| Slow workflow | Check if benchmarks running (--benchmark-skip in tests) |

---

## 📋 Checklist: Ready to Merge?

- [ ] All CI checks green
- [ ] Coverage ≥ previous (check PR comment)
- [ ] No benchmark regressions (check evaluation bundle)
- [ ] Preview deployment looks correct
- [ ] Linting passes (Ruff)
- [ ] Tests pass on Python 3.12 and 3.13
- [ ] Comparison.md reviewed (no unexpected changes)

---

**See [CI_GUIDE.md](CI_GUIDE.md) for detailed documentation.**
