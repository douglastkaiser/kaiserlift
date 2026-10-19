# Client distribution

This directory hosts generated version metadata and the built wheel for static serving. The browser source lives in `kaiserlift/assets/main.js` so it is included in the Python distribution. The wheel is generated in CI and uploaded as a `client-wheel` artifact, so the binary itself is not checked into the repository.

## Rebuild locally
1. Install the build backend with `pip install build` or `uv`.
2. Run `python scripts/inject_version.py` to write the current package version to `client/version.js`. This keeps `main.js` aligned with the Python package.
3. Run `python -m build` (or `uv build`) from the repository root.
4. Copy `dist/kaiserlift-<VERSION>-py3-none-any.whl` to this directory, renaming it to `kaiserlift.whl`.

CI executes `scripts/inject_version.py` before publishing artifacts, so builds always embed the correct version. Contributors should run the same script whenever the Python package version changes to keep the browser metadata in sync with the wheel filename.
