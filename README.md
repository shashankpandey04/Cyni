— **Shashank Pandey**
# ⚡ CYNI — Modular Discord Moderation & Community Bot

[![Built with Python](https://img.shields.io/badge/Built%20With-Python-blue?style=for-the-badge&logo=python)]()
[![Open Source](https://img.shields.io/badge/Open%20Source-Active-green?style=for-the-badge&logo=github)]()
[![Status](https://img.shields.io/badge/Status-Active-yellow?style=for-the-badge)]()

CYNI is a modular, production-minded Discord bot focused on moderation, community tools, and integrations (Roblox, PRC API, analytics). This repository contains the core bot, modular Cogs, utilities, views, and background tasks.

## Why this README is GSoC-focused
This document is tailored for students and mentors evaluating this project for Google Summer of Code (GSoC): it explains the codebase, development setup, contribution guidelines, and proposed project ideas with clear goals and success criteria.

---

## Project Snapshot
- Language: Python 3.10+ (async/await heavy)
- Primary libraries: discord.py (fork), motor (MongoDB), FastAPI, joblib + scikit-learn (ML moderation), uvicorn
- Data store: MongoDB (async via motor)
- Structure: modular `Cogs/` for features, `events/` for Discord events, `Tasks/` for scheduled background work, `Views/` for discord.ui views

Key runtime files:

- `main.py` — simple entry point that calls `run()` from `cyni.py`
- `cyni.py` — bot bootstrap, extension loader, background tasks, and runtime setup
- `requirements.txt` — runtime dependencies

---

## Features (high level)

- Permissions and role checks (staff/management/premium/roblox-specific checks)
- Ticket system (`Views/Tickets.py`) with persistent categories
- Giveaways, vote tracking, LOA handling (background tasks)
- AI-assisted moderation model stored in `Models/modai.py` (joblib)
- Integration with external PRC API and Roblox API

---

## Quick start (developer)

1. Create a Python 3.10+ venv and install dependencies:

```bash
python -m venv .venv
.
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file in the repo root with the following variables (example):

```
DEV_TOKEN=your_dev_token
PRODUCTION_TOKEN=your_production_token
PREMIUM_TOKEN=your_premium_token
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.example.mongodb.net
PRC_API_URL=https://api.example
PRC_API_KEY=secret
```

3. Run the bot (development token preferred):

```bash
python main.py
```

Notes:
- The bot chooses token precedence: `PRODUCTION_TOKEN` > `PREMIUM_TOKEN` > `DEV_TOKEN`.
- The bot uses MongoDB; ensure `MONGO_URI` points to a running MongoDB instance.

---

## Development pointers

- Extensions (Cogs) are auto-loaded from the `Cogs/` folder inside `cyni.py`.
- Background tasks live in `Tasks/` and are started in `setup_hook` during bot setup.
- Database access is via `utils.mongo.Document` abstractions; collections are attached to the bot instance at runtime.
- Machine learning moderation model lives in `Models/modai.py`; model artifact `toxic_model.joblib` is included.

If you plan to work on moderation, start by examining `Models/modai.py`, `utils/automod.py`, and the `Cogs/Moderation.py` cog.

---

## Proposed GSoC Project Ideas

1) Robust Modular Plugin System & Hot-Reloading
- Goal: Harden and document the extension system so new Cogs can be added safely at runtime, with dependency isolation and automatic testing harness for Cogs.
- Success: Prototype a plugin API, add tests for hot-reload behavior, and ship documentation + one sample third-party-style Cog.

2) Scalable Analytics & Command Telemetry
- Goal: Replace current basic analytics with a scalable pipeline (batch writes, retention, time-series views) and provide dashboards/endpoints.
- Success: Implement batched telemetry writes, add a simple FastAPI endpoint for telemetry export, and create a sample dashboard (e.g., Grafana/Prometheus or lightweight web UI).

3) AI-Powered Moderation Improvements
- Goal: Improve the moderation ML pipeline: retraining, dataset versioning, evaluation metrics, and an explainability layer for model decisions.
- Success: Provide a training script, evaluation notebook, and an explainable inference module that returns both label and feature importance.

Mentorship expectations: weekly syncs, review pull requests, define milestones, and provide access to any necessary infrastructure (test MongoDB, bot test guild).

---

## How to contribute

1. Fork the repo and create a feature branch.
2. Open a concise issue describing the problem or feature.
3. Make changes, add tests if applicable, and open a pull request describing the change and its impact.

Tips:
- Keep changes to single concerns per PR.
- Respect existing async patterns and database abstractions.
- Use environment variables for secrets; do not commit tokens.

---

## Contact & Community

Maintainer: Shashank Pandey

For GSoC inquiries, open an issue titled `GSoC: <topic>` and tag the maintainer; include a short proposal and timeline.

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
