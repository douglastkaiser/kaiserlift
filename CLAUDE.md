# CLAUDE.md

## Project Overview

KaiserLift is a data-driven fitness analysis tool for lifting and running performance visualization. It uses Pareto front analysis and Riegel's formula to generate training targets and speed curves.

## Development Commands

- **Install**: `pip install -e ".[dev]"`
- **Tests**: `pytest tests`
- **Lint**: `uvx ruff check --fix .`
- **Format**: `uvx ruff format .`

## Pre-commit

Always run `uvx ruff check --fix . && uvx ruff format .` before committing to catch lint errors that CI will enforce. The pre-commit config is in `.pre-commit-config.yaml` but hooks may not be installed locally.
