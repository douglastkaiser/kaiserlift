# Client distribution

This directory hosts the built wheel for static serving. The wheel is generated in CI and uploaded as a `client-wheel` artifact, so the binary itself is not checked into the repository.

## Rebuild locally
1. Install the build backend with `pip install build` or `uv`.
2. Run `python -m build` (or `uv build`) from the repository root.
3. Copy `dist/kaiserlift-<VERSION>-py3-none-any.whl` to this directory as `kaiserlift.whl` if you need a local copy.
