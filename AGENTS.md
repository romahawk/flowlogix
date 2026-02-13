# AGENTS.md

## Backend Runbook
- Create venv: `python -m venv .venv`
- Activate (Windows): `.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Migrate DB: `flask db upgrade`
- Run app: `python run.py`

## API Docs
- Primary API contract: `docs/api/api-v1.md`
- Architecture docs: `docs/architecture/`
- ADRs: `docs/adr/`

## Branching Rules
- Use feature branches from `main`.
- Keep commits small and scoped (`chore`, `docs`, `fix`, `feat`).
- Avoid force-push on shared branches.

## Demo Credentials
- Demo account is seeded in demo mode: `demo / demo1234`.
- Confirm current demo-mode flags in `.env` before external demos.
