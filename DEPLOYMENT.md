# Deployment Setup

This document explains how the KaiserLift project deploys to GitHub Pages.

## Overview

KaiserLift deploys to `douglastkaiser.github.io` under the `/kaiserlift` subdirectory, allowing the main domain to remain hosted from the `douglastkaiser/douglastkaiser.github.io` repository while this repo manages only its subdirectory.

## Deployment Structure

### Main Deployment (Production)
- **Trigger**: Push to `main` branch
- **Workflow**: `.github/workflows/deploy-to-pages.yml`
- **Destination**: `douglastkaiser.github.io/kaiserlift/`
- **URLs**:
  - Landing: https://www.douglastkaiser.com/kaiserlift/
  - Lifting: https://www.douglastkaiser.com/kaiserlift/lifting/
  - Running: https://www.douglastkaiser.com/kaiserlift/running/

### PR Preview Deployments
- **Trigger**: Pull request opened/updated
- **Workflow**: `.github/workflows/preview-deployment.yml`
- **Destination**: `douglastkaiser.github.io/kaiserlift/pr-{number}/`
- **URLs**: https://www.douglastkaiser.com/kaiserlift/pr-{number}/
- **Cleanup**: Automatic when PR is closed (`.github/workflows/cleanup-preview.yml`)

## Required GitHub Secrets

### PAGES_DEPLOY_TOKEN
A Personal Access Token (PAT) with permissions to push to the `douglastkaiser/douglastkaiser.github.io` repository.

**To create this token:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure:
   - **Name**: `kaiserlift-pages-deploy`
   - **Expiration**: 1 year (or custom)
   - **Repository access**: Only select repositories → `douglastkaiser/douglastkaiser.github.io`
   - **Permissions**:
     - Repository permissions:
       - Contents: Read and write
4. Generate token and copy it
5. Add to this repository's secrets:
   - Go to `douglastkaiser/kaiserlift` → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PAGES_DEPLOY_TOKEN`
   - Value: [paste the token]

**Fallback**: If `PAGES_DEPLOY_TOKEN` is not configured, workflows will attempt to use the default `GITHUB_TOKEN`, but this will fail when trying to push to the external repository.

## How It Works

### Main Deployment Flow

1. **Build Phase**:
   - Install dependencies via `uv`
   - Inject version info into client files
   - Preprocess CSV data for optimal loading
   - Generate HTML files:
     - `index.html` (landing page)
     - `lifting/index.html` (lifting demo)
     - `running/index.html` (running demo)

2. **Deploy Phase**:
   - Clone `douglastkaiser/douglastkaiser.github.io` repo
   - Clear `/kaiserlift` directory
   - Copy new build files to `/kaiserlift`
   - Commit and push changes
   - Retry logic handles concurrent deployments

### PR Preview Flow

1. **Build Phase**: Same as main deployment

2. **Deploy Phase**:
   - Clone `douglastkaiser/douglastkaiser.github.io` repo
   - Create/update `/kaiserlift/pr-{number}` directory
   - Copy preview files
   - Commit and push
   - Post comment on PR with preview links

3. **Cleanup Phase** (on PR close):
   - Remove `/kaiserlift/pr-{number}` directory from external repo
   - Remove `pr-{number}` directory from local gh-pages branch

## File Structure in External Repo

```
douglastkaiser.github.io/
├── index.html              (your main site)
├── projects/               (your projects)
├── ...                     (other main site files)
└── kaiserlift/             (managed by this repo)
    ├── index.html          (landing page)
    ├── lifting/
    │   └── index.html
    ├── running/
    │   └── index.html
    ├── main.js
    ├── version.js
    ├── pr-123/             (preview deployments)
    │   ├── index.html
    │   ├── lifting/
    │   └── running/
    └── pr-456/
        └── ...
```

## Troubleshooting

### 404 Errors on Deployment

If you see 404 errors after deployment:

1. **Check the external repo**: Visit https://github.com/douglastkaiser/douglastkaiser.github.io and verify the `/kaiserlift` directory exists with the expected files
2. **Check GitHub Pages settings**: Ensure GitHub Pages is enabled for `douglastkaiser.github.io` and serving from the correct branch (usually `main`)
3. **Wait for Pages rebuild**: GitHub Pages may take 1-2 minutes to rebuild after a push
4. **Check workflow logs**: Review the deployment workflow logs for any errors

### Token Permission Issues

If you see authentication errors:

1. Verify `PAGES_DEPLOY_TOKEN` is configured in repository secrets
2. Check token hasn't expired
3. Verify token has write access to `douglastkaiser/douglastkaiser.github.io`
4. Regenerate token if necessary

### Deployment Conflicts

If deployments fail due to conflicts:

- The workflows include retry logic with exponential backoff
- Failed pushes will automatically pull latest changes and retry
- Maximum 4 retry attempts with 2s, 4s, 8s, 16s delays

## Manual Deployment

To manually trigger a deployment:

1. Go to Actions → "Deploy to GitHub Pages"
2. Click "Run workflow"
3. Select branch (usually `main`)
4. Click "Run workflow"

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
