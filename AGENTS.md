# AGENTS

This repository uses the following best practices for contributions:

- **Enforce linting & formatting** – leverage the existing pre-commit setup for Ruff (`ruff-check` for linting and `ruff-format` for automatic formatting) to ensure code consistency before committing.
- **Write tests for new features and bug fixes** – place them under `tests/`, keep them deterministic, and run the full test suite (`pytest`) before pushing.
- **Use clear commit messages** – describe the problem and solution in the subject line, reference issues or PR numbers when available, and avoid committing unrelated changes.
- **Prefer small, focused pull requests** – limit each PR to a single feature or fix, include a concise summary, and document any user-facing changes.
- **Favor readability** – follow PEP 8 naming conventions, keep functions small with clear responsibilities, and use type hints plus docstrings for public methods.
- **Document public APIs and behavior changes** – update README or docstrings when adding or modifying user-facing functionality.
- **Run the pre-commit hooks locally before committing** – this mirrors CI checks and catches formatting or lint issues early.
- **Maintain a clean Git history** – rebase onto the latest `main` branch as needed and avoid unnecessary merge commits.
