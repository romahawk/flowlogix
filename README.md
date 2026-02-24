# FlowLogix

**Supply-chain operations tracker for small logistics teams.**
One deterministic dashboard to manage every order's transit state — filtered,
sorted, and RBAC-scoped server-side. No spreadsheet required.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange)

---

## What It Does

- Track orders through their full lifecycle: **Orders → Warehouse → Delivered**
- Filter and sort by status, year, buyer, transport, and free-text search
- Visualize delivery cadence on a **week-indexed timeline chart**
- Role-based access: **Admin** (full CRUD) vs **Viewer** (read-only)
- JSON API v1 with strict validation and structured error envelopes
- Demo mode: auto-seeds data, auto-logs in, blocks all writes — safe to share publicly

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.1, SQLAlchemy 2.0, Flask-Login, Alembic |
| Frontend (production) | Jinja2 + Vanilla JS |
| Frontend (experimental) | React 18 + Vite (`frontend-react/`) |
| Database | SQLite (local/demo) — swappable via `DATABASE_URL` |
| Deploy | Gunicorn (`Procfile`), Render / Railway compatible |

---

## Quick Start (Local)

**Requirements:** Python 3.11+

```bash
# 1. Clone and create environment
git clone <repo-url>
cd flowlogix
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env: set a real SECRET_KEY for production

# 4. Run migrations and start
flask db upgrade
python run.py
```

Open `http://127.0.0.1:5000` — demo mode auto-logs in as `demo / demo1234`.

### Run React Frontend (Experimental)

```bash
cd frontend-react
npm install
npm run dev          # http://127.0.0.1:5173
# Backend must be running on port 5000
```

---

## Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo1234` | Admin (read-only in demo mode) |

---

## API v1

```
GET /api/v1/orders          # Paginated, filtered, RBAC-scoped order list
GET /api/v1/auth/me         # Current user identity and role
```

Full API reference: [`docs/api/api-v1.md`](docs/api/api-v1.md)

---

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/PRD.md`](docs/PRD.md) | Product requirements, killer feature, MVP scope, risks |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, data flow, tradeoffs |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Weekly outcomes, milestones, freeze list |
| [`docs/DECISIONS_LOG.md`](docs/DECISIONS_LOG.md) | Architecture decision records (ADRs) |
| [`docs/api/api-v1.md`](docs/api/api-v1.md) | API v1 contract and parameter reference |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branch conventions, PR discipline, commit rules |

---

## Project Structure

```
flowlogix/
├── app/
│   ├── api/v1/          # JSON API blueprint (orders, auth, schemas, errors)
│   ├── routes/          # Legacy Jinja2 route handlers
│   ├── static/          # CSS + JS (dashboard.js, analytics.js)
│   ├── templates/       # Jinja2 HTML templates
│   ├── models.py        # SQLAlchemy ORM models
│   └── __init__.py      # App factory (demo mode, seeding, guards)
├── frontend-react/      # Experimental React + Vite SPA
├── migrations/          # Alembic migration scripts
├── docs/                # PRD, Architecture, Roadmap, ADRs, API contract
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
├── run.py               # Development server entrypoint
├── wsgi.py              # Gunicorn entrypoint
└── Procfile             # Render / Railway / Heroku process definition
```

---

## Current State

- Sprint 1 complete: API v1 read layer live and hardened.
- Sprint 2 complete: Legacy dashboard modernization baseline (timeline, pagination).
- Sprint 3 next: JS modularization + first test coverage.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full outcome-based roadmap.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch naming, commit conventions, and PR checklist.
