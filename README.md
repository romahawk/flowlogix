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
- Frontend (migration): React + Vite (`frontend-react/`)
- Data: SQLite for local/demo

## Run Backend Locally
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

## Run React Frontend (Sprint 2)
1. Start backend first on `http://127.0.0.1:5000`.
2. Install frontend dependencies:
```bash
cd frontend-react
npm install
```
3. Start Vite dev server:
```bash
npm run dev
```
4. Open `http://127.0.0.1:5173`.

Notes:
- Dev proxy forwards `/api/*` and `/login` to Flask.
- Session auth is cookie-based; log in via backend if unauthorized.

## Documentation
- Roadmap: `docs/roadmap.md`
- UX/UI Spec: `docs/ux-ui-spec.md`
- API Contract: `docs/api/api-v1.md`
- ADRs: `docs/adr/`
- Architecture: `docs/architecture/`
- Sprints: `docs/sprints/`
- Archive: `docs/_archive/`
