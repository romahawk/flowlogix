# FlowLogix - Supply Tracker Dashboard

FlowLogix is an API-first logistics operations platform evolving from a legacy Flask/Jinja dashboard to a React frontend on top of hardened Flask API contracts.

## Current State
- Sprint 1 complete: API v1 read layer is live and hardened.
- Sprint 2 in progress: React foundation consuming API v1.

## API v1
- `GET /api/v1/orders`
- `GET /api/v1/auth/me`

## Tech Stack
- Backend: Flask, SQLAlchemy, Flask-Login, Alembic
- Frontend (legacy): Jinja2 + JS
- Frontend (migration): React (Sprint 2+)
- Data: SQLite for local/demo

## Run Locally
1. Create env and install deps:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
2. Configure env:
```bash
copy .env.example .env
```
3. Run migrations and start app:
```bash
flask db upgrade
python run.py
```

## Documentation
- Roadmap: `docs/roadmap.md`
- UX/UI Spec: `docs/ux-ui-spec.md`
- API Contract: `docs/api/api-v1.md`
- ADRs: `docs/adr/`
- Architecture: `docs/architecture/`
- Sprints: `docs/sprints/`
- Archive: `docs/_archive/`
