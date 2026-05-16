# Contributing to CYNI

Thank you for your interest in contributing to CYNI. This document describes how to get the project running locally, the preferred workflow, and guidelines for code quality and pull requests.

## Getting started

1. Fork the repository and clone your fork.
2. Create and activate a Python 3.10+ virtual environment.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your tokens and `MONGO_URI`. Do not commit secrets.

## Branching & commits

- Work on feature branches named like `feat/<short-description>` or `fix/<short-description>`.
- Keep commits small and focused. Use imperative messages (e.g., "Add ticket view tests").
- Squash or rebase as appropriate before opening a PR.

## Code style and testing

- Follow existing async patterns and the repository's style.
- Use type hints where practical and prefer explicit variable names.
- Add tests for new behavior when possible. If you change DB schemas, include a migration or compatibility notes.

Recommended commands (optional tooling not required by repo):

```bash
# Run your unit tests (if present)
pytest

# Format with black (recommended)
black .
```

## Adding a new Cog / Extension

- Place new feature modules in the `Cogs/` folder and name them clearly.
- Register any runtime configuration or collections inside `cyni.py`'s `setup_hook` pattern or Document abstraction in `utils.mongo`.
- Start background tasks from `Tasks/` via `setup_hook` or a dedicated startup method.

## Pull request process

1. Open an issue first for non-trivial work to discuss design and get approval.
2. Create a branch from `main` and implement your changes.
3. Run tests and update `requirements.txt` only if you add new runtime dependencies.
4. Open a PR with a clear description, list of changes, rationale, and testing steps.
5. Address maintainer feedback; keep PR scope limited to one logical change.

## Issues

- When opening an issue, include reproduction steps, environment details, and expected vs actual behavior.
- Tag the issue as `bug`, `enhancement`, or `discussion`.

## Security

- Do not post secrets or tokens in issues or PRs. If you discover a security vulnerability, contact the maintainer privately (open an issue and mark it confidential) or use the repository's security contact if available.

## Code of Conduct

Contributors are expected to follow a respectful and collaborative code of conduct. Be constructive, polite, and responsive to review comments.

## Contact

If you need help or want to propose a GSoC project, open an issue titled `GSoC: <topic>` with your proposal summary and timeline.

Thanks for contributing!
