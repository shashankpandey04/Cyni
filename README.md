# ⚡ CYNI — Modular Discord Moderation & Community Bot

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

CYNI is a personal, open-source Discord bot built for moderation, community management, and third‑party integrations (Roblox, PRC API). The project emphasizes modular Cogs, background Tasks, and modern async patterns.

Table of contents
- [Features](#features)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Development](#development)
- [Project structure](#project-structure)
- [Testing & CI](#testing--ci)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [License](#license)
- [Contact](#contact)

---

## Features

- Role-based permissions and management helpers
- Ticket system with persistent categories
- Background jobs: giveaways, LOA checks, vote tracking, analytics
- ML-assisted moderation (`Models/modai.py`) with model artifact
- Integrations: PRC API client, Roblox client, FastAPI endpoints

---

## Quick start

Prerequisites: Python 3.10+, Git, and access to a MongoDB instance.

1. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/shashankpandey04/Cyni.git
cd Cyni
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` from `.env.example` and fill in values (do NOT commit secrets):

```text
DEV_TOKEN=your_dev_token
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.example.mongodb.net
PRC_API_URL=https://api.erlc.gg/
PRC_API_KEY=your_prc_api_key
```

3. Run the bot locally:

```bash
python main.py
```

Notes:
- Token precedence: `PRODUCTION_TOKEN` > `PREMIUM_TOKEN` > `DEV_TOKEN`.
- Use a disposable/test bot token and development MongoDB for local testing.

---

## Configuration

- Environment variables: the bot reads secrets from environment variables and `.env` via `python-dotenv`.
- Database: MongoDB is used via `motor`; ensure `MONGO_URI` points to a running instance.
- API keys: Provide `PRC_API_URL`, `PRC_API_KEY`, and any Roblox credentials required for integrations.

Add or update keys in `.env.example` and never commit real tokens.

---

## Development

- Extensions (Cogs) are discovered and loaded from the `Cogs/` directory in `cyni.py`.
- Background scheduled work is defined under `Tasks/` and started in `setup_hook`.
- Database collections are attached to the bot using `utils.mongo.Document`.

Recommended workflow:

1. Fork and branch from `main`.
2. Open an issue describing the change (use templates).
3. Implement changes, add tests where relevant, and open a pull request.

See `CONTRIBUTING.md` for details.

---

## Project structure

- `cyni.py` — Bot bootstrap, extension loading, and lifecycle hooks
- `main.py` — Simple entrypoint
- `Cogs/` — Feature modules (discord cogs)
- `events/` — Event handlers
- `Tasks/` — Background tasks and schedulers
- `Views/` — discord.ui view implementations (tickets, modals)
- `utils/` — Helper utilities (mongo, API clients, automod)
- `Models/` — ML models and artifacts

---

## Testing & CI

- Tests: Add tests under `tests/` and run with `pytest`.
- CI: Add GitHub Actions workflows under `.github/workflows/` for linting and tests (there is an example lint workflow in the repo templates).

Run tests locally:

```bash
pytest
```

---

## Roadmap

- Migrate PRC integration to v2 (`api.erlc.gg`) and add integration tests
- Replace custom `cycord` wrapper with official Discord Views v2
- Add telemetry batching and a lightweight dashboard
- Improve ML retraining workflow and explainability

---

## Contributing

Please read `CONTRIBUTING.md` before opening issues or PRs. Use issue templates for bug reports, feature requests, documentation, and migrations.

---

## Code of Conduct

Be respectful. This project follows a standard Code of Conduct — open issues if you need to discuss behavior or moderation policies.

---

## License

This repository is licensed under the Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Contact

Maintainer: Shashank Pandey

For collaboration, feature requests, or GSoC proposals, open an issue using templates or reach out via GitHub.

---

## Features

- Role-based permissions and management utilities
- Ticketing system with persistent categories
- Background tasks: giveaways, LOA checks, vote tracking
- ML-assisted moderation (`Models/modai.py`)
- Integrations: PRC API, Roblox

---

## Quick start

1. Create and activate a Python 3.10+ virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in values (do not commit secrets). Required variables include `DEV_TOKEN`, `MONGO_URI`, `PRC_API_URL`, and `PRC_API_KEY`.

3. Run the bot locally:

```bash
python main.py
```

Notes:
- Token precedence: `PRODUCTION_TOKEN` > `PREMIUM_TOKEN` > `DEV_TOKEN`.
- Use a development MongoDB instance for local testing.

---

## Development

- Extensions (Cogs) are auto-discovered and loaded from `Cogs/` in `cyni.py`.
- Background tasks live in `Tasks/` and are started during `setup_hook`.
- Database collections are attached to the bot via `utils.mongo.Document`.
- If working on moderation, inspect `Models/modai.py`, `utils/automod.py`, and `Cogs/Moderation.py`.

See `CONTRIBUTING.md` for contribution guidelines and PR workflow.

---

## Documentation & Issues

Use the issue templates when opening new issues (bug, feature, documentation, migration). For proposed large changes (migrations, API updates), include a migration plan and testing steps.

---

## License

This project is licensed under the Apache License, Version 2.0 — see [LICENSE](LICENSE).
