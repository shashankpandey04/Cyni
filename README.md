# ⚡ CYNI — Modular Discord Moderation & Community Bot

[![Built with Python](https://img.shields.io/badge/Built%20With-Python-blue?style=for-the-badge&logo=python)]()
[![Open Source](https://img.shields.io/badge/Open%20Source-Active-green?style=for-the-badge&logo=github)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)]()

CYNI is a personal, open-source Discord bot focused on moderation, community tools, and integrations (Roblox, PRC API, analytics). The codebase is organized for modular development: `Cogs/` for features, `events/` for event handlers, `Tasks/` for scheduled work, and `Views/` for UI interactions.

## Overview

- Language: Python 3.10+
- Primary libraries: discord.py (async), motor (MongoDB), FastAPI, joblib + scikit-learn
- Data store: MongoDB (async via motor)

Key files:
- `main.py` — entrypoint
- `cyni.py` — bot bootstrap, extension loader, and startup logic
- `requirements.txt` — dependencies

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

---

If you want me to expand any section (examples, `.env.example`, docs), tell me which part to focus on.
