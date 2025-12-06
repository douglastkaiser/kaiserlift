# Deployment Setup

This document explains how the KaiserLift project deploys to GitHub Pages.

## Overview

KaiserLift uses GitHub Actions with the official GitHub Pages deployment actions to deploy directly to the repository's GitHub Pages. The site is accessible via custom domain at `www.douglastkaiser.com/kaiserlift/`.

## Deployment Structure

### Main Deployment (Production)
- **Trigger**: Push to `main` branch
- **Workflow**: `.github/workflows/main.yml` (generate-example-html job)
- **Method**: Official GitHub Pages actions (`actions/deploy-pages`)
- **URLs**:
  - Landing: https://www.douglastkaiser.com/kaiserlift/
  - Lifting: https://www.douglastkaiser.com/kaiserlift/lifting/
  - Running: https://www.douglastkaiser.com/kaiserlift/running/

### PR Preview Deployments
- **Trigger**: Pull request opened/updated
- **Workflow**: `.github/workflows/preview-deployment.yml`
- **Method**: Builds both main site + PR preview, deploys together
- **URLs**: https://www.douglastkaiser.com/kaiserlift/pr-{number}/
- **Cleanup**: Automatic when PR is closed (`.github/workflows/cleanup-preview.yml`)

## How It Works

### Main Deployment Flow

1. **Build Phase** (in `main.yml`):
   - Install dependencies via `uv`
   - Inject version info into client files
   - Preprocess CSV data for optimal loading
   - Generate HTML files:
     - `index.html` (landing page)
     - `lifting/index.html` (lifting demo)
     - `running/index.html` (running demo)

2. **Deploy Phase** (main branch only):
   - Configure GitHub Pages (`actions/configure-pages`)
   - Upload build artifact (`actions/upload-pages-artifact`)
   - Deploy to GitHub Pages (`actions/deploy-pages`)

### PR Preview Flow

1. **Build Phase**:
   - Build main site from `main` branch
   - Build PR preview from PR branch
   - Combine into single deployment directory

2. **Deploy Phase**:
   - Deploy combined site (main + PR preview) to GitHub Pages
   - Post comment on PR with preview links

3. **Cleanup Phase** (on PR close):
   - Redeploy main site only (removes PR preview)

## File Structure (Generated)

```
tests/example_use/build/
├── index.html          (landing page)
├── lifting/
│   └── index.html      (lifting demo)
├── running/
│   └── index.html      (running demo)
├── main.js             (client JavaScript)
├── version.js          (version info)
└── .nojekyll           (bypass Jekyll processing)
```

## Troubleshooting

### 404 Errors on Deployment

If you see 404 errors after deployment:

1. **Check GitHub Pages settings**: Go to repository Settings → Pages and verify:
   - Source is set to "GitHub Actions"
   - Custom domain is configured if using one
2. **Wait for Pages rebuild**: GitHub Pages may take 1-2 minutes to rebuild
3. **Check workflow logs**: Review the deployment workflow logs for any errors
4. **Clear browser cache**: Old cached content may cause issues

### Deployment Not Running

If the main deployment doesn't run after a merge:

1. Verify the workflow trigger: `main.yml` runs on `on: push`
2. Check if there's a concurrency conflict (group: `pages-deployment`)
3. The cleanup-preview workflow also deploys - check if it ran instead
4. Manually trigger by pushing a small change to main

### Concurrency Issues

All Pages deployments use the same concurrency group (`pages-deployment`) to prevent conflicts. Only one deployment can run at a time.

## Local Testing

To test the build locally:

```bash
# Install dependencies
uv sync

# Inject version
uv run --with setuptools-scm python scripts/inject_version.py

# Preprocess data
uv run python scripts/preprocess_data.py

# Generate HTML
uv run python tests/example_use/generate_example_html.py

# View output
ls -la tests/example_use/build/
```

The built files will be in `tests/example_use/build/` and can be served with any local HTTP server:

```bash
cd tests/example_use/build
python -m http.server 8000
# Visit http://localhost:8000
```
